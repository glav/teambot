"""Tests for AcceptanceTestExecutor."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from teambot.orchestration.acceptance_test_executor import (
    AcceptanceTestExecutor,
    AcceptanceTestScenario,
    AcceptanceTestStatus,
    extract_commands_from_steps,
    generate_acceptance_test_report,
    parse_acceptance_tests,
)


class TestParseAcceptanceTests:
    """Tests for parsing acceptance tests from feature specs."""

    def test_parse_no_acceptance_tests(self) -> None:
        """Returns empty list when no acceptance test section."""
        content = """# Feature Spec

## Overview
This is a feature.

## Requirements
- REQ-001: Do something
"""
        scenarios = parse_acceptance_tests(content)
        assert scenarios == []

    def test_parse_single_scenario(self) -> None:
        """Parses a single acceptance test scenario."""
        content = """# Feature Spec

## Acceptance Test Scenarios

### AT-001: Basic functionality
**Description**: Test basic functionality

**Steps**:
1. Do step one
2. Do step two

**Expected Result**: Things work
"""
        scenarios = parse_acceptance_tests(content)
        assert len(scenarios) == 1
        assert scenarios[0].id == "AT-001"
        assert scenarios[0].name == "Basic functionality"

    def test_parse_multiple_scenarios(self) -> None:
        """Parses multiple acceptance test scenarios."""
        content = """# Feature Spec

## Acceptance Test Scenarios

### AT-001: First test
**Description**: First test description

### AT-002: Second test
**Description**: Second test description

### AT-003: Third test
**Description**: Third test description
"""
        scenarios = parse_acceptance_tests(content)
        assert len(scenarios) == 3
        assert scenarios[0].id == "AT-001"
        assert scenarios[1].id == "AT-002"
        assert scenarios[2].id == "AT-003"

    def test_parse_scenario_with_steps(self) -> None:
        """Parses scenario with numbered steps."""
        content = """# Feature Spec

## Acceptance Test Scenarios

### AT-001: Test with steps
**Steps**:
1. First step
2. Second step
3. Third step

**Expected Result**: All steps complete
"""
        scenarios = parse_acceptance_tests(content)
        assert len(scenarios) == 1
        assert len(scenarios[0].steps) == 3
        assert "First step" in scenarios[0].steps[0]


class TestExtractCommandsFromSteps:
    """Tests for extracting commands from test steps."""

    def test_no_commands(self) -> None:
        """Returns empty list when no commands in steps."""
        steps = [
            "Do something manually",
            "Check the result",
        ]
        commands = extract_commands_from_steps(steps)
        assert commands == []

    def test_single_command(self) -> None:
        """Extracts single command from step."""
        steps = [
            "Execute `@pm create a plan` to generate plan",
        ]
        commands = extract_commands_from_steps(steps)
        assert len(commands) == 1
        assert commands[0]["command"] == "@pm create a plan"

    def test_multiple_commands(self) -> None:
        """Extracts multiple commands from steps."""
        steps = [
            "Run `@pm plan the work`",
            "Then run `@ba analyze $pm`",
        ]
        commands = extract_commands_from_steps(steps)
        assert len(commands) == 2
        assert commands[0]["command"] == "@pm plan the work"
        assert commands[1]["command"] == "@ba analyze $pm"

    def test_wait_detection(self) -> None:
        """Detects wait keyword in step."""
        steps = [
            "Run `@pm task` and wait for completion",
        ]
        commands = extract_commands_from_steps(steps)
        assert len(commands) == 1
        assert commands[0]["wait_for_completion"] is True

    def test_no_wait_by_default(self) -> None:
        """Commands don't wait by default."""
        steps = [
            "Run `@pm task` immediately",
        ]
        commands = extract_commands_from_steps(steps)
        assert len(commands) == 1
        assert commands[0]["wait_for_completion"] is False


class TestAcceptanceTestScenario:
    """Tests for AcceptanceTestScenario dataclass."""

    def test_default_status(self) -> None:
        """Scenario starts with PENDING status."""
        scenario = AcceptanceTestScenario(id="AT-001", name="Test", description="")
        assert scenario.status == AcceptanceTestStatus.PENDING

    def test_scenario_fields(self) -> None:
        """Scenario stores all fields correctly."""
        scenario = AcceptanceTestScenario(
            id="AT-001",
            name="Test scenario",
            description="Description text",
            preconditions=["Precond 1"],
            steps=["Step 1", "Step 2"],
            expected_result="Expected result",
        )
        assert scenario.id == "AT-001"
        assert scenario.name == "Test scenario"
        assert scenario.description == "Description text"
        assert len(scenario.preconditions) == 1
        assert len(scenario.steps) == 2


class TestAcceptanceTestExecutor:
    """Tests for AcceptanceTestExecutor class."""

    @pytest.fixture
    def spec_with_tests(self) -> str:
        """Feature spec with acceptance tests."""
        return """# Feature Spec

## Acceptance Test Scenarios

### AT-001: Basic test
**Steps**:
1. Execute `@pm test task`

**Expected Result**: Output received
"""

    @pytest.fixture
    def spec_without_tests(self) -> str:
        """Feature spec without acceptance tests."""
        return """# Feature Spec

## Overview
Just a simple spec.
"""

    def test_load_scenarios_from_content(self, spec_with_tests: str) -> None:
        """Loads scenarios from provided content."""
        executor = AcceptanceTestExecutor(spec_content=spec_with_tests)
        scenarios = executor.load_scenarios()
        assert len(scenarios) == 1
        assert scenarios[0].id == "AT-001"

    def test_no_scenarios_found(self, spec_without_tests: str) -> None:
        """Returns empty list when no scenarios in spec."""
        executor = AcceptanceTestExecutor(spec_content=spec_without_tests)
        scenarios = executor.load_scenarios()
        assert scenarios == []

    @pytest.mark.asyncio
    async def test_execute_all_with_no_scenarios(
        self, spec_without_tests: str
    ) -> None:
        """Execute returns result with zero counts when no scenarios."""
        executor = AcceptanceTestExecutor(spec_content=spec_without_tests)
        mock_client = AsyncMock()

        result = await executor.execute_all(mock_client)

        assert result.total == 0
        assert result.passed == 0
        assert result.failed == 0


class TestGenerateReport:
    """Tests for acceptance test report generation."""

    def test_report_with_passed_tests(self) -> None:
        """Report shows passed tests correctly."""
        from teambot.orchestration.acceptance_test_executor import (
            AcceptanceTestResult,
        )

        scenario = AcceptanceTestScenario(
            id="AT-001",
            name="Test",
            description="Test description",
            status=AcceptanceTestStatus.PASSED,
        )
        result = AcceptanceTestResult(
            total=1,
            passed=1,
            failed=0,
            skipped=0,
            scenarios=[scenario],
        )

        report = generate_acceptance_test_report(result)

        assert "PASSED" in report
        assert "AT-001" in report
        assert "1/1" in report or "100%" in report

    def test_report_with_failed_tests(self) -> None:
        """Report shows failed tests with failure reason."""
        from teambot.orchestration.acceptance_test_executor import (
            AcceptanceTestResult,
        )

        scenario = AcceptanceTestScenario(
            id="AT-001",
            name="Test",
            description="Test description",
            status=AcceptanceTestStatus.FAILED,
            failure_reason="Expected output not found",
        )
        result = AcceptanceTestResult(
            total=1,
            passed=0,
            failed=1,
            skipped=0,
            scenarios=[scenario],
        )

        report = generate_acceptance_test_report(result)

        assert "failed" in report.lower()
        assert "AT-001" in report
        assert "Expected output not found" in report

    def test_report_summary(self) -> None:
        """Report includes summary statistics."""
        from teambot.orchestration.acceptance_test_executor import (
            AcceptanceTestResult,
        )

        result = AcceptanceTestResult(
            total=5,
            passed=3,
            failed=2,
            skipped=0,
            scenarios=[],
        )

        report = generate_acceptance_test_report(result)

        assert "5" in report  # total
        assert "3" in report  # passed
        assert "2" in report  # failed


class TestRuntimeValidation:
    """Tests for runtime validation of acceptance tests."""

    @pytest.fixture
    def spec_with_commands(self) -> str:
        """Feature spec with executable commands in steps."""
        return """# Feature Spec

## Acceptance Test Scenarios

### AT-001: Simple command execution
**Description**: Test command execution

**Steps**:
1. Execute `@pm tell a joke`
2. Verify output received

**Expected Result**: PM agent responds with output
"""

    @pytest.fixture
    def spec_with_references(self) -> str:
        """Feature spec with agent reference commands."""
        return """# Feature Spec

## Acceptance Test Scenarios

### AT-001: Reference another agent
**Description**: Test agent reference syntax

**Steps**:
1. Execute `@pm tell a joke`
2. Execute `@ba review $pm`

**Expected Result**: BA agent receives PM's output
"""

    @pytest.mark.asyncio
    async def test_runtime_validation_executes_commands(
        self, spec_with_commands: str
    ) -> None:
        """Runtime validation actually executes extracted commands via TaskExecutor."""
        executor = AcceptanceTestExecutor(spec_content=spec_with_commands)
        executor.load_scenarios()

        mock_client = AsyncMock()
        # TaskExecutor uses .execute() method
        mock_client.execute.return_value = "Why did the PM cross the road?"

        await executor._execute_runtime_validation(mock_client)

        # Verify command was executed via TaskExecutor -> TaskManager -> sdk.execute
        mock_client.execute.assert_called()
        call_args = mock_client.execute.call_args
        assert call_args[0][0] == "pm"  # agent_id

    @pytest.mark.asyncio
    async def test_runtime_validation_passes_on_successful_execution(
        self, spec_with_commands: str
    ) -> None:
        """Runtime validation passes when commands execute successfully."""
        executor = AcceptanceTestExecutor(spec_content=spec_with_commands)
        executor.load_scenarios()

        mock_client = AsyncMock()
        # Return output that matches expected result keywords
        mock_client.execute.return_value = "PM agent responds with output"

        result = await executor._execute_runtime_validation(mock_client)

        assert result.passed >= 1
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_runtime_validation_with_references(
        self, spec_with_references: str
    ) -> None:
        """Runtime validation works with $agent references when using TaskExecutor."""
        executor = AcceptanceTestExecutor(spec_content=spec_with_references)
        executor.load_scenarios()

        mock_client = AsyncMock()
        # TaskExecutor stores PM's output, then BA can reference it
        mock_client.execute.side_effect = [
            "Here's a joke about PMs!",  # PM response - stored by TaskExecutor
            "Reviewing PM's joke - looks good!",  # BA response
        ]

        await executor._execute_runtime_validation(mock_client)

        # With TaskExecutor, PM's output is stored and BA can access it via $pm
        # The second call should receive the injected PM output
        assert mock_client.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_runtime_validation_skips_scenario_without_commands(self) -> None:
        """Scenarios without executable commands are skipped."""
        spec = """# Feature Spec

## Acceptance Test Scenarios

### AT-001: Manual test
**Description**: This is a manual test

**Steps**:
1. Manually verify something
2. Check the results

**Expected Result**: Manual verification complete
"""
        executor = AcceptanceTestExecutor(spec_content=spec)
        executor.load_scenarios()

        mock_client = AsyncMock()

        result = await executor._execute_runtime_validation(mock_client)

        assert result.skipped == 1
        assert result.failed == 0
        # No commands should have been executed
        mock_client.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_merge_results_runtime_failure_overrides_code_pass(self) -> None:
        """Runtime failure overrides code test pass."""
        from teambot.orchestration.acceptance_test_executor import (
            AcceptanceTestResult,
        )

        executor = AcceptanceTestExecutor(spec_content="")

        # Code tests passed
        code_scenario = AcceptanceTestScenario(
            id="AT-001",
            name="Test",
            description="Test",
            status=AcceptanceTestStatus.PASSED,
        )
        code_result = AcceptanceTestResult(
            total=1, passed=1, failed=0, skipped=0, scenarios=[code_scenario]
        )

        # Runtime failed
        runtime_scenario = AcceptanceTestScenario(
            id="AT-001-runtime",
            name="Test (Runtime)",
            description="Test",
            status=AcceptanceTestStatus.FAILED,
            failure_reason="Feature doesn't work at runtime",
        )
        runtime_result = AcceptanceTestResult(
            total=1, passed=0, failed=1, skipped=0, scenarios=[runtime_scenario]
        )

        merged = executor._merge_validation_results(code_result, runtime_result)

        # Runtime failure should override code pass
        assert merged.failed == 1
        assert merged.passed == 0
        assert "RUNTIME VALIDATION FAILED" in merged.scenarios[0].failure_reason
