"""Acceptance test executor for file-based orchestration.

Parses acceptance test scenarios from feature specifications and validates
them via code-level testing (pytest) rather than live REPL execution.

The executor asks the builder agent to write and run pytest tests that
validate each acceptance scenario. This ensures:
1. Tests exercise the actual implemented code
2. Failures provide actionable debugging info
3. Fixes can be verified by re-running the same tests
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


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
    """Validates acceptance tests via code-level testing.

    This executor:
    1. Parses acceptance test scenarios from the feature spec
    2. Builds a validation prompt for the builder agent
    3. Asks the builder to write and run pytest tests for each scenario
    4. Parses the output to determine pass/fail status
    5. Reports detailed results for debugging
    """

    def __init__(
        self,
        spec_path: Path | None = None,
        spec_content: str | None = None,
        timeout: float = 300.0,  # Longer timeout for pytest runs
        on_progress: Callable[[str, dict], None] | None = None,
    ):
        """Initialize the executor.

        Args:
            spec_path: Path to the feature spec file.
            spec_content: Direct spec content (alternative to spec_path).
            timeout: Timeout for the validation run in seconds.
            on_progress: Callback for progress updates.
        """
        self.spec_path = spec_path
        self.spec_content = spec_content
        self.timeout = timeout
        self.on_progress = on_progress
        self.scenarios: list[AcceptanceTestScenario] = []
        self.validation_output: str = ""

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
        """Execute acceptance test validation via code-level testing.

        Instead of executing commands against a live REPL, this method:
        1. Builds a prompt with all acceptance scenarios
        2. Asks the builder to write/run pytest tests for each
        3. Parses the output to determine which scenarios passed/failed

        Args:
            sdk_client: The SDK client to use for the builder agent.

        Returns:
            AcceptanceTestResult with scenario results.
        """
        if not self.scenarios:
            self.load_scenarios()

        if not self.scenarios:
            return AcceptanceTestResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                scenarios=[],
            )

        if self.on_progress:
            self.on_progress("acceptance_test_validation_start", {
                "total_scenarios": len(self.scenarios),
            })

        # Build the validation prompt
        prompt = self._build_validation_prompt()

        # Execute via builder agent
        try:
            self.validation_output = await asyncio.wait_for(
                sdk_client.execute_streaming("builder-1", prompt, None),
                timeout=self.timeout,
            )
        except TimeoutError:
            self.validation_output = "ERROR: Validation timed out"
            for scenario in self.scenarios:
                scenario.status = AcceptanceTestStatus.ERROR
                scenario.failure_reason = "Validation timed out"

            return AcceptanceTestResult(
                total=len(self.scenarios),
                passed=0,
                failed=len(self.scenarios),
                skipped=0,
                scenarios=self.scenarios,
            )

        # Parse the validation output to determine results
        return self._parse_validation_results()

    def _build_validation_prompt(self) -> str:
        """Build a prompt asking the builder to validate acceptance scenarios.

        Returns:
            The validation prompt for the builder agent.
        """
        scenario_text = []
        for scenario in self.scenarios:
            scenario_text.append(f"""
### {scenario.id}: {scenario.name}

**Description**: {scenario.description}

**Steps**:
{chr(10).join(f"  {i+1}. {step}" for i, step in enumerate(scenario.steps))}

**Expected Result**: {scenario.expected_result}

**Verification**: {scenario.verification}
""")

        return f"""# Acceptance Test Validation

You must validate the implemented feature by writing and running pytest tests.

## Instructions

1. For EACH acceptance scenario below, write a pytest test that validates the functionality
2. Run the tests using `uv run pytest` with the specific test file
3. Report the results in the EXACT format specified below

## Acceptance Scenarios to Validate

{"".join(scenario_text)}

## Required Output Format

After running the tests, you MUST output a results block in this EXACT format:

```acceptance-results
{chr(10).join(f"{s.id}: PASSED" for s in self.scenarios)}
```

Replace PASSED with FAILED if a test fails, and add a failure reason:
```
AT-001: FAILED - Reason: assertion error on line 42
```

## Validation Process

1. First, examine the existing test files to understand the testing patterns
2. Create or update test file(s) for these acceptance scenarios
3. Run the tests: `uv run pytest tests/test_acceptance_<feature>.py -v`
4. Parse the pytest output to determine pass/fail for each scenario
5. Output the results block with the status of each scenario

## Important

- Tests must actually exercise the implemented code, not mock everything
- Each acceptance scenario should map to at least one test function
- If a scenario cannot be tested (e.g., missing implementation), mark it FAILED with reason
- Include the actual pytest output so failures can be debugged

Begin validation now.
"""

    def _parse_validation_results(self) -> AcceptanceTestResult:
        """Parse the builder's validation output to determine results.

        Returns:
            AcceptanceTestResult with parsed scenario statuses.
        """
        passed = 0
        failed = 0
        skipped = 0

        # Look for the acceptance-results block
        results_pattern = r"```acceptance-results\n(.*?)```"
        results_match = re.search(results_pattern, self.validation_output, re.DOTALL)

        if results_match:
            results_text = results_match.group(1)
            self._parse_results_block(results_text)
        else:
            # No structured results - try to infer from pytest output
            self._infer_results_from_output()

        # Count results
        for scenario in self.scenarios:
            if scenario.status == AcceptanceTestStatus.PASSED:
                passed += 1
            elif scenario.status in (AcceptanceTestStatus.FAILED, AcceptanceTestStatus.ERROR):
                failed += 1
            elif scenario.status == AcceptanceTestStatus.SKIPPED:
                skipped += 1
            else:
                # Still pending = treat as failed (no validation done)
                scenario.status = AcceptanceTestStatus.FAILED
                scenario.failure_reason = "No validation result reported"
                failed += 1

        return AcceptanceTestResult(
            total=len(self.scenarios),
            passed=passed,
            failed=failed,
            skipped=skipped,
            scenarios=self.scenarios,
        )

    def _parse_results_block(self, results_text: str) -> None:
        """Parse the structured results block.

        Args:
            results_text: The text inside the acceptance-results block.
        """
        for line in results_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Parse lines like "AT-001: PASSED" or "AT-002: FAILED - Reason: ..."
            pattern = r"(AT-\d+):\s*(PASSED|FAILED|SKIPPED)(?:\s*-\s*(.*))?"
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                scenario_id = match.group(1).upper()
                status = match.group(2).upper()
                reason = match.group(3) or ""

                # Find the matching scenario
                for scenario in self.scenarios:
                    if scenario.id == scenario_id:
                        if status == "PASSED":
                            scenario.status = AcceptanceTestStatus.PASSED
                        elif status == "FAILED":
                            scenario.status = AcceptanceTestStatus.FAILED
                            scenario.failure_reason = reason or "Test failed"
                        elif status == "SKIPPED":
                            scenario.status = AcceptanceTestStatus.SKIPPED
                            scenario.failure_reason = reason or "Test skipped"
                        break

    def _infer_results_from_output(self) -> None:
        """Infer test results from pytest output when no structured block exists.

        This is a fallback that looks for pytest patterns in the output.
        """
        output_lower = self.validation_output.lower()

        # Check for overall pytest failure patterns
        all_passed = (
            "passed" in output_lower and
            "failed" not in output_lower and
            "error" not in output_lower
        )

        # Look for specific test failures mentioning scenario IDs
        for scenario in self.scenarios:
            scenario_id_lower = scenario.id.lower()

            # Check if this specific scenario is mentioned as failing
            if f"{scenario_id_lower}" in output_lower:
                # Look for failure indicators near the scenario ID
                scenario_section = self._extract_scenario_section(scenario.id)

                if "fail" in scenario_section or "error" in scenario_section:
                    scenario.status = AcceptanceTestStatus.FAILED
                    scenario.failure_reason = self._extract_failure_reason(scenario_section)
                elif "pass" in scenario_section or "ok" in scenario_section:
                    scenario.status = AcceptanceTestStatus.PASSED
                elif "skip" in scenario_section:
                    scenario.status = AcceptanceTestStatus.SKIPPED
                else:
                    # Mentioned but unclear - check overall status
                    if all_passed:
                        scenario.status = AcceptanceTestStatus.PASSED
                    else:
                        scenario.status = AcceptanceTestStatus.FAILED
                        scenario.failure_reason = "Status unclear from output"
            else:
                # Scenario not mentioned - check if tests were even run
                if "0 passed" in output_lower or "no tests" in output_lower:
                    scenario.status = AcceptanceTestStatus.FAILED
                    scenario.failure_reason = "No tests were run for this scenario"
                elif all_passed:
                    scenario.status = AcceptanceTestStatus.PASSED
                else:
                    scenario.status = AcceptanceTestStatus.FAILED
                    scenario.failure_reason = "Could not determine status from output"

    def _extract_scenario_section(self, scenario_id: str) -> str:
        """Extract the section of output related to a specific scenario.

        Args:
            scenario_id: The scenario ID to search for.

        Returns:
            The relevant section of output, or empty string.
        """
        # Find text around the scenario ID mention
        pattern = rf".{{0,200}}{re.escape(scenario_id)}.{{0,500}}"
        match = re.search(pattern, self.validation_output, re.IGNORECASE | re.DOTALL)
        return match.group(0).lower() if match else ""

    def _extract_failure_reason(self, section: str) -> str:
        """Extract a failure reason from a section of output.

        Args:
            section: The section to search.

        Returns:
            A failure reason string.
        """
        # Look for common assertion error patterns
        patterns = [
            r"assert(?:ion)?(?:error)?[:\s]+(.{1,100})",
            r"error[:\s]+(.{1,100})",
            r"failed[:\s]+(.{1,100})",
        ]

        for pattern in patterns:
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]

        return "Test failed (see output for details)"


def generate_acceptance_test_report(
    result: AcceptanceTestResult,
    validation_output: str = "",
) -> str:
    """Generate a markdown report of acceptance test results.

    Args:
        result: The test results.
        validation_output: Optional raw output from the validation run.

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
        status_col = f"{status_emoji} {scenario.status.value}"
        lines.append(f"| {scenario.id} | {scenario.name} | {status_col} | {details} |")

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
            if scenario.status in (AcceptanceTestStatus.FAILED, AcceptanceTestStatus.ERROR):
                lines.extend([
                    f"### {scenario.id}: {scenario.name}",
                    "",
                    f"**Failure Reason**: {scenario.failure_reason}",
                    "",
                    f"**Expected**: {scenario.expected_result}",
                    "",
                ])

        # Include validation output for debugging
        if validation_output:
            lines.extend([
                "## Validation Output (for debugging)",
                "",
                "```",
                validation_output[:5000] if len(validation_output) > 5000 else validation_output,
                "```",
                "",
            ])

    return "\n".join(lines)
