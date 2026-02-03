"""Acceptance test executor for file-based orchestration.

Parses acceptance test scenarios from feature specifications and executes
them against a live REPL instance to validate implementation correctness.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class AcceptanceTestStatus(Enum):
    """Status of an acceptance test execution."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class AcceptanceTestScenario:
    """A single acceptance test scenario parsed from the spec."""

    id: str
    name: str
    description: str
    preconditions: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    expected_result: str = ""
    verification: str = ""
    status: AcceptanceTestStatus = AcceptanceTestStatus.PENDING
    actual_result: str = ""
    failure_reason: str = ""


@dataclass
class AcceptanceTestResult:
    """Result of executing all acceptance tests."""

    total: int
    passed: int
    failed: int
    skipped: int
    scenarios: list[AcceptanceTestScenario]

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and self.passed == self.total

    @property
    def summary(self) -> str:
        """Generate a summary of the test results."""
        status = "✅ ALL PASSED" if self.all_passed else "❌ FAILURES"
        return f"{status}: {self.passed}/{self.total} passed, {self.failed} failed"


def parse_acceptance_tests(spec_content: str) -> list[AcceptanceTestScenario]:
    """Parse acceptance test scenarios from a feature specification.

    Args:
        spec_content: The markdown content of the feature spec.

    Returns:
        List of parsed acceptance test scenarios.
    """
    scenarios: list[AcceptanceTestScenario] = []

    # Find the Acceptance Test Scenarios section
    section_pattern = r"##\s*\d*\.?\s*Acceptance Test Scenarios\s*\n(.*?)(?=\n##\s|\Z)"
    section_match = re.search(section_pattern, spec_content, re.DOTALL | re.IGNORECASE)

    if not section_match:
        return scenarios

    section_content = section_match.group(1)

    # Parse individual scenarios (AT-001, AT-002, etc.)
    scenario_pattern = r"###\s*(AT-\d+):\s*([^\n]+)\n(.*?)(?=\n###\s*AT-|\Z)"
    scenario_matches = re.finditer(scenario_pattern, section_content, re.DOTALL)

    for match in scenario_matches:
        scenario_id = match.group(1).strip()
        scenario_name = match.group(2).strip()
        scenario_body = match.group(3).strip()

        scenario = AcceptanceTestScenario(
            id=scenario_id,
            name=scenario_name,
            description=_extract_field(scenario_body, "Description"),
        )

        # Parse preconditions
        preconditions = _extract_field(scenario_body, "Preconditions")
        if preconditions:
            scenario.preconditions = [p.strip() for p in preconditions.split(",")]

        # Parse steps
        steps_match = re.search(
            r"\*\*Steps\*\*:?\s*\n((?:\d+\.\s+[^\n]+\n?)+)",
            scenario_body,
            re.IGNORECASE,
        )
        if steps_match:
            steps_text = steps_match.group(1)
            scenario.steps = re.findall(r"\d+\.\s+(.+)", steps_text)

        # Parse expected result
        scenario.expected_result = _extract_field(scenario_body, "Expected Result")

        # Parse verification
        scenario.verification = _extract_field(scenario_body, "Verification")

        scenarios.append(scenario)

    return scenarios


def _extract_field(text: str, field_name: str) -> str:
    """Extract a field value from scenario body."""
    pattern = rf"\*\*{field_name}\*\*:?\s*([^\n]+(?:\n(?!\*\*)[^\n]+)*)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def extract_commands_from_steps(steps: list[str]) -> list[dict]:
    """Extract executable commands from test steps.

    Args:
        steps: List of step descriptions.

    Returns:
        List of command dicts with 'command' and 'wait_for_completion' keys.
    """
    commands = []
    # Pattern to match commands in backticks like `@pm task` or `@ba analyze $pm`
    command_pattern = r"`(@[a-zA-Z][a-zA-Z0-9-]*\s+[^`]+)`"

    for step in steps:
        matches = re.findall(command_pattern, step)
        for cmd in matches:
            # Check if step mentions waiting
            wait = "wait" in step.lower() or "completion" in step.lower()
            commands.append({
                "command": cmd.strip(),
                "wait_for_completion": wait,
                "step": step,
            })

    return commands


class AcceptanceTestExecutor:
    """Executes acceptance tests against a live REPL instance.

    This executor:
    1. Parses acceptance test scenarios from the feature spec
    2. Spawns a REPL subprocess (or uses an existing one)
    3. Executes each scenario's steps
    4. Validates outputs against expected results
    5. Reports pass/fail status
    """

    def __init__(
        self,
        spec_path: Path | None = None,
        spec_content: str | None = None,
        timeout: float = 60.0,
        on_progress: Callable[[str, dict], None] | None = None,
    ):
        """Initialize the executor.

        Args:
            spec_path: Path to the feature spec file.
            spec_content: Direct spec content (alternative to spec_path).
            timeout: Timeout for each test scenario in seconds.
            on_progress: Callback for progress updates.
        """
        self.spec_path = spec_path
        self.spec_content = spec_content
        self.timeout = timeout
        self.on_progress = on_progress
        self.scenarios: list[AcceptanceTestScenario] = []

    def load_scenarios(self) -> list[AcceptanceTestScenario]:
        """Load and parse acceptance test scenarios from the spec.

        Returns:
            List of parsed scenarios.
        """
        content = self.spec_content
        if not content and self.spec_path:
            content = self.spec_path.read_text()

        if not content:
            return []

        self.scenarios = parse_acceptance_tests(content)
        return self.scenarios

    async def execute_all(
        self,
        sdk_client,
    ) -> AcceptanceTestResult:
        """Execute all acceptance test scenarios.

        Args:
            sdk_client: The SDK client to use for executing commands.

        Returns:
            AcceptanceTestResult with all scenario results.
        """
        if not self.scenarios:
            self.load_scenarios()

        passed = 0
        failed = 0
        skipped = 0

        for scenario in self.scenarios:
            if self.on_progress:
                self.on_progress("acceptance_test_start", {
                    "id": scenario.id,
                    "name": scenario.name,
                })

            try:
                scenario.status = AcceptanceTestStatus.RUNNING
                result = await self._execute_scenario(scenario, sdk_client)

                if result:
                    scenario.status = AcceptanceTestStatus.PASSED
                    passed += 1
                else:
                    scenario.status = AcceptanceTestStatus.FAILED
                    failed += 1

            except asyncio.TimeoutError:
                scenario.status = AcceptanceTestStatus.FAILED
                scenario.failure_reason = f"Timeout after {self.timeout}s"
                failed += 1

            except Exception as e:
                scenario.status = AcceptanceTestStatus.ERROR
                scenario.failure_reason = str(e)
                failed += 1

            if self.on_progress:
                self.on_progress("acceptance_test_complete", {
                    "id": scenario.id,
                    "status": scenario.status.value,
                    "failure_reason": scenario.failure_reason,
                })

        return AcceptanceTestResult(
            total=len(self.scenarios),
            passed=passed,
            failed=failed,
            skipped=skipped,
            scenarios=self.scenarios,
        )

    async def _execute_scenario(
        self,
        scenario: AcceptanceTestScenario,
        sdk_client,
    ) -> bool:
        """Execute a single acceptance test scenario.

        This method extracts commands from the scenario steps and executes
        them against the SDK client, then validates the results.

        Args:
            scenario: The scenario to execute.
            sdk_client: The SDK client.

        Returns:
            True if the scenario passed, False otherwise.
        """
        commands = extract_commands_from_steps(scenario.steps)

        if not commands:
            # No executable commands found - mark as skipped
            scenario.failure_reason = "No executable commands found in steps"
            return False

        outputs: list[str] = []

        for cmd_info in commands:
            command = cmd_info["command"]

            # Parse the command to extract agent and content
            agent_match = re.match(r"@([a-zA-Z][a-zA-Z0-9-]*)\s+(.+)", command)
            if not agent_match:
                continue

            agent_id = agent_match.group(1)
            content = agent_match.group(2)

            try:
                # Execute the command
                output = await asyncio.wait_for(
                    sdk_client.execute_streaming(agent_id, content, None),
                    timeout=self.timeout,
                )
                outputs.append(output)
                scenario.actual_result += f"\n[{agent_id}]: {output[:500]}..."

                # If step says to wait, add a small delay
                if cmd_info["wait_for_completion"]:
                    await asyncio.sleep(0.5)

            except asyncio.TimeoutError:
                scenario.failure_reason = f"Command timed out: {command}"
                return False

        # Validate results
        return self._validate_scenario_result(scenario, outputs)

    def _validate_scenario_result(
        self,
        scenario: AcceptanceTestScenario,
        outputs: list[str],
    ) -> bool:
        """Validate scenario outputs against expected results.

        Args:
            scenario: The scenario with expected results.
            outputs: List of actual outputs from commands.

        Returns:
            True if validation passes, False otherwise.
        """
        if not outputs:
            scenario.failure_reason = "No outputs captured"
            return False

        # For basic validation, check if expected result keywords appear in outputs
        expected = scenario.expected_result.lower()
        combined_output = " ".join(outputs).lower()

        # Check for explicit failure indicators
        failure_indicators = [
            "error",
            "not found",
            "no results",
            "don't see",
            "cannot find",
            "missing",
        ]

        # If expected result mentions error handling, failure indicators are OK
        expects_error = "error" in expected or "no results" in expected

        if not expects_error:
            for indicator in failure_indicators:
                if indicator in combined_output and indicator not in expected:
                    scenario.failure_reason = f"Output indicates failure: '{indicator}' found"
                    return False

        # Check verification criteria if specified
        if scenario.verification:
            verification_keywords = re.findall(r"[a-zA-Z]+", scenario.verification.lower())
            # At least some verification keywords should appear in output
            found = sum(1 for kw in verification_keywords if kw in combined_output)
            if found < len(verification_keywords) * 0.3:  # At least 30% match
                scenario.failure_reason = "Verification criteria not met in output"
                return False

        return True


def generate_acceptance_test_report(result: AcceptanceTestResult) -> str:
    """Generate a markdown report of acceptance test results.

    Args:
        result: The test results.

    Returns:
        Markdown formatted report.
    """
    lines = [
        "# Acceptance Test Results",
        "",
        f"**Status**: {result.summary}",
        "",
        "## Scenarios",
        "",
        "| ID | Name | Status | Details |",
        "|-----|------|--------|---------|",
    ]

    for scenario in result.scenarios:
        status_emoji = {
            AcceptanceTestStatus.PASSED: "✅",
            AcceptanceTestStatus.FAILED: "❌",
            AcceptanceTestStatus.SKIPPED: "⏭️",
            AcceptanceTestStatus.ERROR: "💥",
            AcceptanceTestStatus.PENDING: "⏳",
            AcceptanceTestStatus.RUNNING: "🔄",
        }.get(scenario.status, "❓")

        details = scenario.failure_reason or "-"
        lines.append(
            f"| {scenario.id} | {scenario.name} | {status_emoji} {scenario.status.value} | {details} |"
        )

    lines.extend([
        "",
        "## Summary",
        "",
        f"- **Total**: {result.total}",
        f"- **Passed**: {result.passed}",
        f"- **Failed**: {result.failed}",
        f"- **Skipped**: {result.skipped}",
        "",
    ])

    if not result.all_passed:
        lines.extend([
            "## Failed Scenarios",
            "",
        ])
        for scenario in result.scenarios:
            if scenario.status == AcceptanceTestStatus.FAILED:
                lines.extend([
                    f"### {scenario.id}: {scenario.name}",
                    "",
                    f"**Failure Reason**: {scenario.failure_reason}",
                    "",
                    f"**Expected**: {scenario.expected_result}",
                    "",
                    f"**Actual**: {scenario.actual_result[:500] if scenario.actual_result else 'No output'}",
                    "",
                ])

    return "\n".join(lines)
