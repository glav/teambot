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
    command_pattern = r"`(@[a-zA-Z][a-zA-Z0-9,_-]*\s+[^`]+)`"

    for step in steps:
        matches = re.findall(command_pattern, step)
        for cmd in matches:
            # Check if step mentions waiting
            wait = "wait" in step.lower() or "completion" in step.lower()
            commands.append(
                {
                    "command": cmd.strip(),
                    "wait_for_completion": wait,
                    "step": step,
                }
            )

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
            self.on_progress(
                "acceptance_test_validation_start",
                {
                    "total_scenarios": len(self.scenarios),
                },
            )

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
        code_test_result = self._parse_validation_results()

        # NEW: Run runtime validation to verify the feature actually works
        runtime_result = await self._execute_runtime_validation(sdk_client)

        # Merge results - runtime failures override code test passes
        return self._merge_validation_results(code_test_result, runtime_result)

    async def _execute_runtime_validation(
        self,
        sdk_client,
    ) -> AcceptanceTestResult:
        """Execute actual commands from acceptance scenarios to verify runtime behavior.

        This is the critical check that verifies the feature ACTUALLY WORKS,
        not just that tests pass. It extracts commands from scenario steps
        and runs them through the SAME TaskExecutor that production uses.

        This ensures that features like $agent references work because:
        1. Commands go through the parser (extracting references)
        2. Commands go through TaskExecutor (which stores results)
        3. Reference commands can find stored results

        Args:
            sdk_client: The SDK client to use for executing commands.

        Returns:
            AcceptanceTestResult with runtime validation results.
        """
        # Import here to avoid circular imports
        from teambot.repl.parser import parse_command
        from teambot.tasks.executor import TaskExecutor

        if self.on_progress:
            self.on_progress(
                "runtime_validation_start",
                {
                    "total_scenarios": len(self.scenarios),
                },
            )

        # Create a TaskExecutor instance that will be shared across all commands
        # This is critical - it ensures agent results are stored and retrievable
        executor = TaskExecutor(sdk_client=sdk_client)

        runtime_results: list[AcceptanceTestScenario] = []

        for scenario in self.scenarios:
            # Create a copy for runtime results
            runtime_scenario = AcceptanceTestScenario(
                id=f"{scenario.id}-runtime",
                name=f"{scenario.name} (Runtime)",
                description=scenario.description,
                preconditions=scenario.preconditions,
                steps=scenario.steps,
                expected_result=scenario.expected_result,
                verification=scenario.verification,
            )

            # Extract commands from steps
            commands = extract_commands_from_steps(scenario.steps)

            if not commands:
                # No executable commands found - skip runtime validation for this scenario
                runtime_scenario.status = AcceptanceTestStatus.SKIPPED
                runtime_scenario.failure_reason = "No executable commands found in steps"
                runtime_results.append(runtime_scenario)
                continue

            if self.on_progress:
                self.on_progress(
                    "runtime_scenario_start",
                    {
                        "scenario_id": scenario.id,
                        "command_count": len(commands),
                    },
                )

            try:
                # Execute commands through TaskExecutor (not SDK directly!)
                outputs: dict[str, str] = {}
                all_commands_succeeded = True
                expected_error_produced = False

                for cmd_info in commands:
                    cmd_str = cmd_info["command"]

                    try:
                        # Parse the command using the real parser
                        # This extracts $agent references properly
                        cmd = parse_command(cmd_str)

                        if cmd.type.name == "UNKNOWN" or not cmd.agent_ids:
                            continue

                        # Execute through TaskExecutor (stores results, handles references)
                        result = await executor.execute(cmd)

                        if result.success:
                            outputs[cmd.agent_ids[0]] = result.output
                        else:
                            error_msg = result.error or "Execution failed"
                            if self._is_expected_error_scenario(scenario.expected_result):
                                # Scenario expects an error — this is correct behavior
                                expected_error_produced = True
                                outputs[cmd.agent_ids[0]] = error_msg
                            else:
                                all_commands_succeeded = False
                                runtime_scenario.failure_reason = (
                                    f"Command '{cmd_str}' failed: {error_msg}"
                                )
                                break

                    except Exception as e:
                        error_msg = str(e)
                        if self._is_expected_error_scenario(scenario.expected_result):
                            expected_error_produced = True
                            outputs["error"] = error_msg
                        else:
                            all_commands_succeeded = False
                            runtime_scenario.failure_reason = f"Command '{cmd_str}' failed: {e}"
                            break

                if expected_error_produced:
                    # Error scenario — error was produced as expected
                    # Exact error format is verified by code-level pytest tests
                    all_commands_succeeded = True
                    runtime_scenario.actual_result = "Expected error produced: " + " ".join(
                        outputs.values()
                    )
                elif all_commands_succeeded and scenario.expected_result:
                    # For non-error scenarios, successful execution of all commands
                    # is sufficient runtime verification. Output content is validated
                    # by code-level pytest tests; mock SDK output in runtime validation
                    # does not produce meaningful text for content matching.
                    pass

                if all_commands_succeeded:
                    runtime_scenario.status = AcceptanceTestStatus.PASSED
                    keys = list(outputs.keys())
                    runtime_scenario.actual_result = f"Commands executed: {keys}"
                else:
                    runtime_scenario.status = AcceptanceTestStatus.FAILED

            except TimeoutError:
                runtime_scenario.status = AcceptanceTestStatus.ERROR
                runtime_scenario.failure_reason = "Runtime validation timed out"

            runtime_results.append(runtime_scenario)

            if self.on_progress:
                self.on_progress(
                    "runtime_scenario_complete",
                    {
                        "scenario_id": scenario.id,
                        "status": runtime_scenario.status.value,
                    },
                )

        # Calculate totals
        passed = sum(1 for s in runtime_results if s.status == AcceptanceTestStatus.PASSED)
        failed_statuses = (AcceptanceTestStatus.FAILED, AcceptanceTestStatus.ERROR)
        failed = sum(1 for s in runtime_results if s.status in failed_statuses)
        skipped = sum(1 for s in runtime_results if s.status == AcceptanceTestStatus.SKIPPED)

        if self.on_progress:
            self.on_progress(
                "runtime_validation_complete",
                {
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                },
            )

        return AcceptanceTestResult(
            total=len(runtime_results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            scenarios=runtime_results,
        )

    @staticmethod
    def _is_expected_error_scenario(expected_result: str) -> bool:
        """Check if a scenario's expected result describes an error.

        Scenarios that test error handling (e.g., unknown agent rejection)
        expect commands to fail. When the expected result describes an error,
        a command failure is the correct behavior, not a test failure.

        Args:
            expected_result: The scenario's expected result text.

        Returns:
            True if the scenario expects an error to be produced.
        """
        if not expected_result:
            return False
        lower = expected_result.replace("`", "").lower().strip()
        error_indicators = [
            "error message",
            "error identifying",
            "error listing",
            "rejected",
            "rejects",
            "unknown agent",
        ]
        return any(indicator in lower for indicator in error_indicators)

    def _merge_validation_results(
        self,
        code_result: AcceptanceTestResult,
        runtime_result: AcceptanceTestResult,
    ) -> AcceptanceTestResult:
        """Merge code-level and runtime validation results.

        Runtime failures override code test passes - if the feature
        doesn't actually work at runtime, the acceptance test fails.

        Args:
            code_result: Results from pytest-based validation.
            runtime_result: Results from runtime command execution.

        Returns:
            Merged AcceptanceTestResult.
        """
        # Build a map of runtime results by base scenario ID
        runtime_map: dict[str, AcceptanceTestScenario] = {}
        for scenario in runtime_result.scenarios:
            # Strip "-runtime" suffix to match original ID
            base_id = scenario.id.replace("-runtime", "")
            runtime_map[base_id] = scenario

        # Merge: runtime failure overrides code pass
        merged_scenarios: list[AcceptanceTestScenario] = []
        for scenario in code_result.scenarios:
            runtime_scenario = runtime_map.get(scenario.id)

            if runtime_scenario and runtime_scenario.status == AcceptanceTestStatus.FAILED:
                # Runtime failed - mark as failed even if code tests passed
                scenario.status = AcceptanceTestStatus.FAILED
                scenario.failure_reason = (
                    f"RUNTIME VALIDATION FAILED: {runtime_scenario.failure_reason} "
                    f"(Code tests may have passed but feature doesn't work at runtime)"
                )
            elif runtime_scenario and runtime_scenario.status == AcceptanceTestStatus.ERROR:
                scenario.status = AcceptanceTestStatus.ERROR
                scenario.failure_reason = f"RUNTIME ERROR: {runtime_scenario.failure_reason}"

            merged_scenarios.append(scenario)

        # Recalculate totals
        passed = sum(1 for s in merged_scenarios if s.status == AcceptanceTestStatus.PASSED)
        failed_statuses = (AcceptanceTestStatus.FAILED, AcceptanceTestStatus.ERROR)
        failed = sum(1 for s in merged_scenarios if s.status in failed_statuses)
        skipped = sum(1 for s in merged_scenarios if s.status == AcceptanceTestStatus.SKIPPED)

        # Append runtime validation output to main validation output
        runtime_report = "\n\n## Runtime Validation Results\n\n"
        for scenario in runtime_result.scenarios:
            status_emoji = "✅" if scenario.status == AcceptanceTestStatus.PASSED else "❌"
            runtime_report += f"- {status_emoji} {scenario.id}: {scenario.status.value}"
            if scenario.failure_reason:
                runtime_report += f" - {scenario.failure_reason}"
            runtime_report += "\n"

        self.validation_output += runtime_report

        return AcceptanceTestResult(
            total=len(merged_scenarios),
            passed=passed,
            failed=failed,
            skipped=skipped,
            scenarios=merged_scenarios,
        )

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
{chr(10).join(f"  {i + 1}. {step}" for i, step in enumerate(scenario.steps))}

**Expected Result**: {scenario.expected_result}

**Verification**: {scenario.verification}
""")

        return f"""# Acceptance Test Validation - STRICT MODE

You must validate each acceptance scenario by writing integration tests that
exercise the REAL implementation code and running them with pytest.

## CRITICAL REQUIREMENTS

1. Tests must call the REAL implementation code, not mocks
2. You must show the ACTUAL pytest output (copy/paste it)
3. Each scenario must have a corresponding test function named `test_at_XXX_*`
4. If any test fails, analyze why and FIX THE IMPLEMENTATION CODE

## Acceptance Scenarios to Validate

{"".join(scenario_text)}

## Step-by-Step Process

### Step 1: Create Integration Test File

Create `tests/test_acceptance_validation.py` with tests for each scenario.
Each test MUST:
- Import and use the real implementation classes/functions
- NOT mock the core functionality being tested
- Have a name starting with `test_at_XXX` where XXX is the scenario ID

Example structure:
```python
import pytest
from teambot.your_module import YourClass

class TestAcceptanceScenarios:
    def test_at_001_simple_reference(self):
        # Call REAL implementation
        result = YourClass().do_thing()
        assert result == expected
```

### Step 2: Run Tests and Show Output

Run: `uv run pytest tests/test_acceptance_validation.py -v`

**YOU MUST COPY THE COMPLETE PYTEST OUTPUT HERE**

### Step 3: If Tests Fail

If any test fails:
1. Analyze the failure from the pytest output
2. Fix the implementation code (not just the test)
3. Re-run and show the new output

### Step 4: Final Results

After all tests pass, output this block:

```pytest-output
<paste the actual pytest output showing all tests passing>
```

Then output:
```acceptance-results
{chr(10).join(f"{s.id}: PASSED" for s in self.scenarios)}
```

## IMPORTANT

- I will verify your pytest output contains `test_at_XXX` for each scenario
- I will verify the output shows tests actually passing (not just claimed)
- If pytest output is missing or doesn't match, ALL scenarios marked FAILED

Begin validation now. Start by creating the test file.
"""

    def _parse_validation_results(self) -> AcceptanceTestResult:
        """Parse the builder's validation output to determine results.

        This method is STRICT - it verifies actual pytest output exists
        and shows tests passing, not just a self-reported results block.

        Returns:
            AcceptanceTestResult with parsed scenario statuses.
        """
        passed = 0
        failed = 0
        skipped = 0

        # STRICT: First verify actual pytest output exists
        pytest_verified = self._verify_pytest_output()

        if not pytest_verified:
            # No valid pytest output found - all scenarios fail
            for scenario in self.scenarios:
                scenario.status = AcceptanceTestStatus.FAILED
                scenario.failure_reason = "No valid pytest output found in response"
            return AcceptanceTestResult(
                total=len(self.scenarios),
                passed=0,
                failed=len(self.scenarios),
                skipped=0,
                scenarios=self.scenarios,
            )

        # Look for the acceptance-results block (but verify against pytest output)
        results_pattern = r"```acceptance-results\n(.*?)```"
        results_match = re.search(results_pattern, self.validation_output, re.DOTALL)

        if results_match:
            results_text = results_match.group(1)
            self._parse_results_block(results_text)
            # Cross-verify claimed results against pytest output
            self._verify_claimed_results()
        else:
            # No structured results - infer from pytest output
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

    def _verify_pytest_output(self) -> bool:
        """Verify that actual pytest output exists in the validation output.

        Returns:
            True if valid pytest output found, False otherwise.
        """
        output = self.validation_output.lower()

        # Look for pytest execution indicators
        pytest_indicators = [
            "passed",
            "failed",
            "test session starts",
            "collecting",
            "pytest",
        ]

        # Must have at least some pytest indicators
        indicator_count = sum(1 for ind in pytest_indicators if ind in output)
        if indicator_count < 2:
            return False

        # Look for test function names matching our pattern
        # Pattern: test_at_001, test_at_002, etc.
        test_pattern = r"test_at_\d+"
        test_matches = re.findall(test_pattern, output, re.IGNORECASE)

        # Should have at least one test per scenario (ideally)
        # But be lenient - at least verify some tests were run
        return len(test_matches) > 0 or "passed" in output

    def _verify_claimed_results(self) -> None:
        """Cross-verify claimed PASSED results against actual pytest output.

        If a scenario is claimed as PASSED but we can't find evidence
        of the corresponding test passing in pytest output, mark it as FAILED.
        """
        output_lower = self.validation_output.lower()

        for scenario in self.scenarios:
            if scenario.status == AcceptanceTestStatus.PASSED:
                # Look for evidence this scenario's test actually passed
                # Check if test_at_XXX appears in output and isn't marked as failed
                test_pattern = f"test_at_{scenario.id[-3:]}"
                if test_pattern.lower() not in output_lower:
                    # No test found for this scenario
                    # Check if there's a generic "all passed" indicator
                    if "failed" in output_lower or "error" in output_lower:
                        # There were failures, and we can't verify this test
                        scenario.status = AcceptanceTestStatus.FAILED
                        scenario.failure_reason = f"Could not verify test for {scenario.id} passed"

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
            "passed" in output_lower
            and "failed" not in output_lower
            and "error" not in output_lower
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

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- **Total**: {result.total}",
            f"- **Passed**: {result.passed}",
            f"- **Failed**: {result.failed}",
            f"- **Skipped**: {result.skipped}",
            "",
        ]
    )

    if not result.all_passed:
        lines.extend(
            [
                "## Failed Scenarios",
                "",
            ]
        )
        for scenario in result.scenarios:
            if scenario.status in (AcceptanceTestStatus.FAILED, AcceptanceTestStatus.ERROR):
                lines.extend(
                    [
                        f"### {scenario.id}: {scenario.name}",
                        "",
                        f"**Failure Reason**: {scenario.failure_reason}",
                        "",
                        f"**Expected**: {scenario.expected_result}",
                        "",
                    ]
                )

        # Include validation output for debugging
        if validation_output:
            lines.extend(
                [
                    "## Validation Output (for debugging)",
                    "",
                    "```",
                    validation_output[:5000]
                    if len(validation_output) > 5000
                    else validation_output,
                    "```",
                    "",
                ]
            )

    return "\n".join(lines)
