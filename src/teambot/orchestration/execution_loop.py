"""Main execution loop for file-based orchestration."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any

from teambot.orchestration.acceptance_test_executor import (
    AcceptanceTestExecutor,
    AcceptanceTestResult,
    generate_acceptance_test_report,
)
from teambot.orchestration.objective_parser import parse_objective_file
from teambot.orchestration.review_iterator import ReviewIterator, ReviewStatus
from teambot.orchestration.stage_config import (
    ParallelGroupConfig,
    StagesConfiguration,
    load_stages_config,
)
from teambot.orchestration.time_manager import TimeManager
from teambot.workflow.stages import STAGE_METADATA, WorkflowStage


class ExecutionResult(Enum):
    """Result of execution loop."""

    COMPLETE = "complete"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    REVIEW_FAILED = "review_failed"
    ACCEPTANCE_TEST_FAILED = "acceptance_test_failed"
    ERROR = "error"


# Legacy constants for backward compatibility - prefer using StagesConfiguration
REVIEW_STAGES = {
    WorkflowStage.SPEC_REVIEW,
    WorkflowStage.PLAN_REVIEW,
    WorkflowStage.IMPLEMENTATION_REVIEW,
    WorkflowStage.POST_REVIEW,
}

WORK_TO_REVIEW_MAPPING = {
    WorkflowStage.SPEC: WorkflowStage.SPEC_REVIEW,
    WorkflowStage.PLAN: WorkflowStage.PLAN_REVIEW,
    WorkflowStage.IMPLEMENTATION: WorkflowStage.IMPLEMENTATION_REVIEW,
    WorkflowStage.TEST: WorkflowStage.POST_REVIEW,
}

STAGE_AGENTS = {
    WorkflowStage.SETUP: {"work": "pm", "review": None},
    WorkflowStage.BUSINESS_PROBLEM: {"work": "ba", "review": None},
    WorkflowStage.SPEC: {"work": "ba", "review": "reviewer"},
    WorkflowStage.SPEC_REVIEW: {"work": "ba", "review": "reviewer"},
    WorkflowStage.RESEARCH: {"work": "builder-1", "review": None},
    WorkflowStage.TEST_STRATEGY: {"work": "builder-1", "review": None},
    WorkflowStage.PLAN: {"work": "pm", "review": "reviewer"},
    WorkflowStage.PLAN_REVIEW: {"work": "pm", "review": "reviewer"},
    WorkflowStage.IMPLEMENTATION: {"work": "builder-1", "review": "reviewer"},
    WorkflowStage.IMPLEMENTATION_REVIEW: {"work": "builder-1", "review": "reviewer"},
    WorkflowStage.TEST: {"work": "builder-1", "review": None},
    WorkflowStage.POST_REVIEW: {"work": "pm", "review": "reviewer"},
    WorkflowStage.COMPLETE: {"work": None, "review": None},
}

STAGE_ORDER = [
    WorkflowStage.SETUP,
    WorkflowStage.BUSINESS_PROBLEM,
    WorkflowStage.SPEC,
    WorkflowStage.SPEC_REVIEW,
    WorkflowStage.RESEARCH,
    WorkflowStage.TEST_STRATEGY,
    WorkflowStage.PLAN,
    WorkflowStage.PLAN_REVIEW,
    WorkflowStage.IMPLEMENTATION,
    WorkflowStage.IMPLEMENTATION_REVIEW,
    WorkflowStage.TEST,
    WorkflowStage.POST_REVIEW,
    WorkflowStage.COMPLETE,
]


class ExecutionLoop:
    """Main driver for file-based orchestration."""

    def __init__(
        self,
        objective_path: Path,
        config: dict[str, Any],
        teambot_dir: Path,
        max_hours: float = 8.0,
        stages_config: StagesConfiguration | None = None,
    ):
        self.objective = parse_objective_file(objective_path)
        self.objective_path = objective_path
        self.config = config
        self.time_manager = TimeManager(max_seconds=int(max_hours * 3600))
        self.cancelled = False

        # Create feature-specific subdirectory
        self.feature_name = self.objective.feature_name
        self.teambot_dir = teambot_dir / self.feature_name
        self.teambot_dir.mkdir(parents=True, exist_ok=True)

        # Create artifacts subdirectory
        (self.teambot_dir / "artifacts").mkdir(exist_ok=True)

        # Load stages configuration
        if stages_config is not None:
            self.stages_config = stages_config
        else:
            # Try to load from config path or use defaults
            stages_path = config.get("stages_config")
            self.stages_config = load_stages_config(Path(stages_path) if stages_path else None)

        # Current state
        self.current_stage = WorkflowStage.SETUP
        self.stage_outputs: dict[WorkflowStage, str] = {}

        # Parallel group tracking (for resume mid-parallel-group)
        self.parallel_group_status: dict[str, dict[str, Any]] = {}

        # Acceptance test tracking
        self.acceptance_tests_passed: bool = False
        self.acceptance_test_result: AcceptanceTestResult | None = None
        self.acceptance_test_iterations: int = 0
        self._acceptance_test_history: list[dict[str, Any]] = []

        # Will be set during run()
        self.sdk_client: Any = None
        self.review_iterator: ReviewIterator | None = None

    async def run(
        self,
        sdk_client: Any,
        on_progress: Callable[[str, Any], None] | None = None,
    ) -> ExecutionResult:
        """Execute the workflow loop.

        Args:
            sdk_client: CopilotSDKClient for agent execution
            on_progress: Optional callback for progress updates

        Returns:
            ExecutionResult indicating outcome
        """
        self.sdk_client = sdk_client
        self.review_iterator = ReviewIterator(sdk_client, self.teambot_dir)
        self.time_manager.start()

        # Emit orchestration started event
        if on_progress:
            objective_name = (
                self.objective.title
                if hasattr(self.objective, "title") and self.objective.title
                else self.feature_name
            )
            on_progress(
                "orchestration_started",
                {
                    "objective_name": objective_name,
                    "objective_path": str(self.objective_path) if self.objective_path else None,
                },
            )

        try:
            while self.current_stage != WorkflowStage.COMPLETE:
                # Check cancellation
                if self.cancelled:
                    self._emit_completed_event(on_progress, "cancelled")
                    self._save_state(ExecutionResult.CANCELLED)
                    return ExecutionResult.CANCELLED

                # Check timeout
                if self.time_manager.is_expired():
                    self._emit_completed_event(on_progress, "timeout")
                    self._save_state(ExecutionResult.TIMEOUT)
                    return ExecutionResult.TIMEOUT

                stage = self.current_stage

                if on_progress:
                    on_progress("stage_changed", {"stage": stage.name})

                # Execute stage based on type
                stage_config = self.stages_config.stages.get(stage)

                # Check for parallel group first - this triggers when we reach
                # the first stage in a parallel group
                parallel_group = self._get_parallel_group_for_stage(stage)
                if parallel_group:
                    success = await self._execute_parallel_group(parallel_group, on_progress)
                    if not success:
                        self._emit_completed_event(on_progress, "error")
                        self._save_state(ExecutionResult.ERROR)
                        return ExecutionResult.ERROR
                    # Skip to the 'before' stage (e.g., PLAN) after parallel group
                    self.current_stage = parallel_group.before
                    self._save_state()
                    continue  # Skip normal stage advancement

                elif stage in self.stages_config.acceptance_test_stages:
                    # Execute acceptance test stage with retry loop
                    await self._execute_acceptance_test_with_retry(stage, on_progress)
                    if not self.acceptance_tests_passed:
                        self._emit_completed_event(on_progress, "acceptance_test_failed")
                        self._save_state(ExecutionResult.ACCEPTANCE_TEST_FAILED)
                        return ExecutionResult.ACCEPTANCE_TEST_FAILED
                elif stage in self.stages_config.review_stages:
                    # Check if this review requires acceptance tests to have passed
                    if (
                        stage_config
                        and stage_config.requires_acceptance_tests_passed
                        and not self.acceptance_tests_passed
                    ):
                        # Cannot proceed - acceptance tests haven't passed
                        self.stage_outputs[stage] = (
                            "BLOCKED: Cannot proceed with post-review - "
                            "acceptance tests have not been executed or did not pass."
                        )
                        self._emit_completed_event(on_progress, "acceptance_test_failed")
                        self._save_state(ExecutionResult.ACCEPTANCE_TEST_FAILED)
                        return ExecutionResult.ACCEPTANCE_TEST_FAILED

                    result = await self._execute_review_stage(stage, on_progress)
                    if result == ReviewStatus.FAILED:
                        self._emit_completed_event(on_progress, "review_failed")
                        self._save_state(ExecutionResult.REVIEW_FAILED)
                        return ExecutionResult.REVIEW_FAILED
                else:
                    await self._execute_work_stage(stage, on_progress)

                # Advance to next stage
                self.current_stage = self._get_next_stage(stage)

                # Save state after each stage completion for resumability
                self._save_state()

            self._emit_completed_event(on_progress, "complete")
            self._save_state(ExecutionResult.COMPLETE)
            return ExecutionResult.COMPLETE

        except Exception:
            self._emit_completed_event(on_progress, "error")
            self._save_state(ExecutionResult.ERROR)
            raise

    def _emit_completed_event(
        self,
        on_progress: Callable[[str, Any], None] | None,
        status: str,
    ) -> None:
        """Emit orchestration_completed event.

        Args:
            on_progress: Progress callback (may be None)
            status: Completion status (complete, cancelled, timeout, error, etc.)
        """
        if on_progress:
            objective_name = (
                self.objective.title
                if hasattr(self.objective, "title") and self.objective.title
                else self.feature_name
            )
            on_progress(
                "orchestration_completed",
                {
                    "objective_name": objective_name,
                    "status": status,
                    "duration_seconds": self.time_manager.elapsed_seconds,
                },
            )

    def _get_parallel_group_for_stage(self, stage: WorkflowStage) -> ParallelGroupConfig | None:
        """Find parallel group that starts with this stage.

        Only triggers when the stage is the first stage in a parallel group.

        Args:
            stage: Current stage to check

        Returns:
            ParallelGroupConfig if stage is first in a group, None otherwise
        """

        for group in self.stages_config.parallel_groups:
            # Only trigger on the first stage in the group
            if group.stages and stage == group.stages[0]:
                return group
        return None

    async def _execute_parallel_group(
        self,
        group: ParallelGroupConfig,
        on_progress: Callable[[str, Any], None] | None,
    ) -> bool:
        """Execute all stages in a parallel group concurrently.

        Args:
            group: Parallel group configuration
            on_progress: Progress callback

        Returns:
            True if all stages succeeded, False if any failed
        """
        from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor

        if on_progress:
            on_progress(
                "parallel_group_start",
                {
                    "group": group.name,
                    "stages": [s.name for s in group.stages],
                },
            )

        # Filter to only incomplete stages (for resume support)
        stages_to_run = self._filter_incomplete_stages(group)

        if not stages_to_run:
            # All stages already complete
            if on_progress:
                on_progress(
                    "parallel_group_complete",
                    {"group": group.name, "all_success": True},
                )
            return True

        executor = ParallelStageExecutor(max_concurrent=2)
        results = await executor.execute_parallel(
            stages=stages_to_run,
            execution_loop=self,
            on_progress=on_progress,
        )

        # Track results in parallel_group_status
        if group.name not in self.parallel_group_status:
            self.parallel_group_status[group.name] = {"stages": {}}

        for stage, result in results.items():
            self.parallel_group_status[group.name]["stages"][stage.name] = {
                "status": "completed" if result.success else "failed",
                "error": result.error,
            }

        all_success = all(r.success for r in results.values())

        if on_progress:
            on_progress(
                "parallel_group_complete",
                {"group": group.name, "all_success": all_success},
            )

        return all_success

    def _filter_incomplete_stages(self, group: ParallelGroupConfig) -> list[WorkflowStage]:
        """Filter parallel group stages to only those not yet completed.

        Used for resume support - only re-run stages that didn't complete.

        Args:
            group: Parallel group configuration

        Returns:
            List of stages that need to be executed
        """
        if group.name not in self.parallel_group_status:
            # No prior status - run all stages
            return list(group.stages)

        group_status = self.parallel_group_status[group.name]
        stages_status = group_status.get("stages", {})

        incomplete = []
        for stage in group.stages:
            stage_info = stages_status.get(stage.name, {})
            if stage_info.get("status") != "completed":
                incomplete.append(stage)

        return incomplete

    def cancel(self) -> None:
        """Request cancellation of execution."""
        self.cancelled = True

    async def _execute_acceptance_test_stage(
        self,
        stage: WorkflowStage,
        on_progress: Callable[[str, Any], None] | None,
    ) -> AcceptanceTestResult:
        """Execute acceptance test stage via code-level validation.

        This stage:
        1. Finds the feature spec (from artifacts or docs/feature-specs/)
        2. Parses acceptance test scenarios from the spec
        3. Asks the builder to write and run pytest tests for each scenario
        4. Parses results and reports pass/fail status
        """
        if on_progress:
            on_progress("acceptance_test_stage_start", {"stage": stage.name})

        # Find the feature spec
        spec_content = self._find_feature_spec_content()

        if not spec_content:
            # No spec found - create a failing result
            self.acceptance_test_result = AcceptanceTestResult(
                total=0,
                passed=0,
                failed=1,
                skipped=0,
                scenarios=[],
            )
            self.stage_outputs[stage] = (
                "ERROR: Could not find feature specification to extract acceptance test scenarios."
            )
            self.acceptance_tests_passed = False
            return self.acceptance_test_result

        # Create executor and run tests
        executor = AcceptanceTestExecutor(
            spec_content=spec_content,
            timeout=300.0,  # Longer timeout for pytest runs
            on_progress=on_progress,
        )

        executor.load_scenarios()

        if not executor.scenarios:
            # No acceptance tests defined - this is an ERROR (acceptance tests are MANDATORY)
            self.acceptance_test_result = AcceptanceTestResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                scenarios=[],
            )
            self.stage_outputs[stage] = (
                "ERROR: No acceptance test scenarios found in the feature spec. "
                "Acceptance tests are MANDATORY per the specification requirements.\n\n"
                "Action Required:\n"
                "1. Add an 'Acceptance Test Scenarios' section "
                "(heading: ## Acceptance Test Scenarios) to the feature spec\n"
                "2. Include at least one test scenario with the format:\n"
                "   ### Scenario AT-001: [Description]\n"
                "   - Given: [preconditions]\n"
                "   - When: [action]\n"
                "   - Then: [expected result]\n"
                "3. Ensure scenarios test the complete user flow"
            )
            self.acceptance_tests_passed = False  # Block workflow - acceptance tests are mandatory
            return self.acceptance_test_result

        # Execute acceptance tests via code-level validation
        self.acceptance_test_result = await executor.execute_all(self.sdk_client)

        # Store the validation output for debugging and fix context
        self._acceptance_validation_output = executor.validation_output

        # Generate report (include validation output for debugging)
        report = generate_acceptance_test_report(
            self.acceptance_test_result,
            validation_output=executor.validation_output,
        )
        self.stage_outputs[stage] = report

        # Save report to artifacts
        report_path = self.teambot_dir / "artifacts" / "acceptance_test_results.md"
        report_path.write_text(report, encoding="utf-8")

        # Update tracking
        self.acceptance_tests_passed = self.acceptance_test_result.all_passed

        if on_progress:
            on_progress(
                "acceptance_test_stage_complete",
                {
                    "stage": stage.name,
                    "passed": self.acceptance_test_result.passed,
                    "failed": self.acceptance_test_result.failed,
                    "all_passed": self.acceptance_tests_passed,
                },
            )

        return self.acceptance_test_result

    async def _execute_acceptance_test_with_retry(
        self,
        stage: WorkflowStage,
        on_progress: Callable[[str, Any], None] | None,
    ) -> AcceptanceTestResult:
        """Execute acceptance tests with fix-retry loop on failure.

        When acceptance tests fail, this method:
        1. Reviews the failed tests and current implementation
        2. Asks the builder to implement a fix
        3. Re-runs the acceptance tests
        4. Repeats up to MAX_ITERATIONS times

        Args:
            stage: The acceptance test stage
            on_progress: Optional callback for progress updates

        Returns:
            AcceptanceTestResult with final test results
        """
        max_iterations = ReviewIterator.MAX_ITERATIONS
        self.acceptance_test_iterations = 0

        # Track iteration history for state file
        iteration_history: list[dict[str, Any]] = []

        # Accumulated output for stage_outputs
        accumulated_output: list[str] = []

        while self.acceptance_test_iterations < max_iterations:
            self.acceptance_test_iterations += 1

            if on_progress:
                on_progress(
                    "acceptance_test_iteration",
                    {
                        "iteration": self.acceptance_test_iterations,
                        "max_iterations": max_iterations,
                    },
                )

            # Run acceptance tests (output will be accumulated separately)
            result = await self._execute_acceptance_test_stage(stage, on_progress)

            # Get the validation output for this iteration
            validation_output = getattr(self, "_acceptance_validation_output", "")

            # Record this iteration's test results
            iteration_record: dict[str, Any] = {
                "iteration": self.acceptance_test_iterations,
                "passed": result.passed,
                "failed": result.failed,
                "total": result.total,
                "all_passed": result.all_passed,
            }

            # Add test results to accumulated output
            accumulated_output.append(
                f"## Iteration {self.acceptance_test_iterations} - Test Results\n\n"
                f"**Status**: {'✅ PASSED' if result.all_passed else '❌ FAILED'} "
                f"({result.passed}/{result.total} passed)\n\n"
                f"{generate_acceptance_test_report(result, validation_output)}\n\n"
                f"---\n\n"
            )

            if result.all_passed:
                # Tests passed - we're done
                self.acceptance_tests_passed = True
                iteration_record["fix_applied"] = False
                iteration_history.append(iteration_record)
                break

            # Tests failed - if we have iterations left, try to fix
            if self.acceptance_test_iterations >= max_iterations:
                # No more iterations - fail
                iteration_record["fix_applied"] = False
                iteration_history.append(iteration_record)
                if on_progress:
                    on_progress(
                        "acceptance_test_max_iterations_reached",
                        {
                            "iterations_used": self.acceptance_test_iterations,
                        },
                    )
                break

            # Build context for fix
            fix_context = self._build_acceptance_test_fix_context(result)

            if on_progress:
                on_progress(
                    "acceptance_test_fix_start",
                    {
                        "iteration": self.acceptance_test_iterations,
                        "failed_count": result.failed,
                    },
                )

            # Ask builder to implement fix
            fix_output = await self._execute_acceptance_test_fix(fix_context, on_progress)

            # Record the fix
            iteration_record["fix_applied"] = True
            fix_summary = fix_output[:500] + "..." if len(fix_output) > 500 else fix_output
            iteration_record["fix_summary"] = fix_summary
            iteration_history.append(iteration_record)

            # Add fix output to accumulated output
            accumulated_output.append(
                f"## Iteration {self.acceptance_test_iterations} - Fix Attempt\n\n"
                f"{fix_output}\n\n"
                f"---\n\n"
            )

            if on_progress:
                on_progress(
                    "acceptance_test_fix_complete",
                    {
                        "iteration": self.acceptance_test_iterations,
                        "fix_output_length": len(fix_output),
                    },
                )

        # Store the complete history in stage_outputs
        self.stage_outputs[stage] = "\n".join(accumulated_output)

        # Store iteration history for state file
        self._acceptance_test_history = iteration_history

        # Ensure we have a valid result before returning
        # This should always be set by _execute_acceptance_test_stage in the loop above
        if self.acceptance_test_result is None:
            raise RuntimeError(
                "Acceptance test result was not set after execution loop. "
                "This indicates a programming error."
            )

        # Set final pass/fail status
        if not self.acceptance_test_result.all_passed:
            self.acceptance_tests_passed = False

        return self.acceptance_test_result

    def _build_acceptance_test_fix_context(
        self,
        test_result: AcceptanceTestResult,
    ) -> str:
        """Build context for the fix agent based on failed tests.

        Args:
            test_result: The acceptance test result with failures

        Returns:
            Context string for the fix agent
        """
        # Get validation output if available
        validation_output = getattr(self, "_acceptance_validation_output", "")

        parts = [
            "# Acceptance Test Fix Required",
            "",
            "The acceptance tests have **FAILED**. Your task is to analyze "
            "the failures and implement a fix to make the tests pass.",
            "",
            "## Failed Test Results",
            "",
        ]

        # Show failed scenarios
        for scenario in test_result.scenarios:
            if scenario.status.value in ("failed", "error"):
                parts.extend(
                    [
                        f"### {scenario.id}: {scenario.name}",
                        f"**Failure Reason**: {scenario.failure_reason}",
                        f"**Expected**: {scenario.expected_result}",
                        "",
                    ]
                )

        # Include validation output for debugging
        if validation_output:
            parts.extend(
                [
                    "## Previous Validation Output",
                    "",
                    "This is the output from the last validation run.",
                    "Use this to understand what failed:",
                    "",
                    "```",
                    validation_output[:4000]
                    if len(validation_output) > 4000
                    else validation_output,
                    "```",
                    "",
                ]
            )

        parts.extend(
            [
                "## Feature Specification",
                "",
            ]
        )

        # Include feature spec
        spec_content = self._find_feature_spec_content()
        if spec_content:
            parts.append(spec_content[:3000])  # Truncate long specs
        else:
            parts.append("(Feature spec not found)")

        parts.extend(
            [
                "",
                "## Your Task - CRITICAL",
                "",
                "The feature DOES NOT WORK. You must fix the IMPLEMENTATION, not just",
                "write tests that pass. The acceptance tests validate real user behavior.",
                "",
                "1. **Read** the failed test output to understand what's broken",
                "2. **Find** the implementation code that handles this feature",
                "3. **Fix** the actual implementation bug (not test expectations)",
                "4. **Run** `uv run pytest tests/test_acceptance_validation.py -v`",
                "5. **Show** the actual pytest output proving tests pass",
                "",
                "## Verification",
                "",
                "After fixing, you MUST include:",
                "",
                "1. The code changes you made (show the diff or key changes)",
                "2. The actual pytest output (copy/paste the terminal output)",
                "3. A results block:",
                "",
                "```acceptance-results",
            ]
        )

        for scenario in test_result.scenarios:
            parts.append(f"{scenario.id}: PASSED  # or FAILED - Reason: ...")

        parts.extend(
            [
                "```",
                "",
                "WARNING: If you claim PASSED but the pytest output shows failures,",
                "or if pytest output is missing, all scenarios will be marked FAILED.",
                "",
            ]
        )

        return "\n".join(parts)

    async def _execute_acceptance_test_fix(
        self,
        context: str,
        on_progress: Callable[[str, Any], None] | None,
    ) -> str:
        """Execute the fix implementation agent.

        Args:
            context: The fix context including failed tests and implementation
            on_progress: Optional callback for progress updates

        Returns:
            The fix agent's output
        """
        # Use builder-1 as the fix agent (same as implementation)
        fix_agent = "builder-1"

        if on_progress:
            on_progress("agent_running", {"agent_id": fix_agent, "task": "fix_acceptance_tests"})

        output = await self.sdk_client.execute_streaming(fix_agent, context, None)

        if on_progress:
            on_progress("agent_complete", {"agent_id": fix_agent})

        return output

    def _find_feature_spec_content(self) -> str | None:
        """Find and load the feature specification content.

        Searches in order:
        1. .teambot/{feature}/artifacts/feature_spec.md
        2. docs/feature-specs/*.md (matching feature name)
        """
        # Check artifacts directory first
        artifacts_spec = self.teambot_dir / "artifacts" / "feature_spec.md"
        if artifacts_spec.exists():
            return artifacts_spec.read_text(encoding="utf-8")

        # Check docs/feature-specs/
        feature_specs_dir = self.teambot_dir.parent.parent / "docs" / "feature-specs"
        if feature_specs_dir.exists():
            # Normalize feature name for case-insensitive matching
            normalized_feature = self.feature_name.replace("-", "").lower()
            for spec_file in feature_specs_dir.glob("*.md"):
                # Case-insensitive matching with hyphens removed
                normalized_spec = spec_file.stem.replace("-", "").lower()
                if normalized_feature in normalized_spec:
                    return spec_file.read_text(encoding="utf-8")

        return None

    async def _execute_work_stage(
        self,
        stage: WorkflowStage,
        on_progress: Callable[[str, Any], None] | None,
    ) -> str:
        """Execute a non-review work stage."""
        agents = self.stages_config.get_stage_agents(stage)
        work_agent = agents.get("work")

        if not work_agent:
            return ""

        if on_progress:
            on_progress("agent_running", {"agent_id": work_agent, "task": stage.name})

        # Build context from objective, persona, and prior stage outputs
        context = self._build_stage_context(stage, work_agent)

        # Execute the agent
        output = await self.sdk_client.execute_streaming(work_agent, context, None)

        # Store output for later stages
        self.stage_outputs[stage] = output

        if on_progress:
            on_progress("agent_complete", {"agent_id": work_agent})

        return output

    async def _execute_review_stage(
        self,
        stage: WorkflowStage,
        on_progress: Callable[[str, Any], None] | None,
    ) -> ReviewStatus:
        """Execute a review stage with iteration."""
        agents = self.stages_config.get_stage_agents(stage)
        work_agent = agents.get("work") or "builder-1"
        review_agent = agents.get("review") or "reviewer"

        if not self.review_iterator:
            raise RuntimeError("ReviewIterator not initialized")

        context = self._build_stage_context(stage, review_agent)

        def review_progress(msg: str) -> None:
            if on_progress:
                on_progress("review_progress", {"stage": stage.name, "message": msg})

        result = await self.review_iterator.execute(
            stage=stage,
            work_agent=work_agent,
            review_agent=review_agent,
            context=context,
            on_progress=review_progress,
        )

        # Store review output for this stage
        if result.final_output:
            self.stage_outputs[stage] = result.final_output

        return result.status

    def _build_stage_context(self, stage: WorkflowStage, agent_id: str | None = None) -> str:
        """Build context for a stage from objective and prior outputs.

        Custom agents in .github/agents/ handle persona enforcement.
        This method focuses on workflow stage context only.

        Args:
            stage: The current workflow stage
            agent_id: The agent executing this stage (unused, kept for API compat)

        Returns:
            Complete context string with objective and stage information
        """
        stage_config = self.stages_config.stages.get(stage)
        parts: list[str] = []

        # Load and include prompt template if specified
        prompt_content = self._load_prompt_template(stage_config)
        if prompt_content:
            parts.append(prompt_content)
            parts.append("")

        # Conditionally include objective content based on include_objective flag
        include_objective = stage_config.include_objective if stage_config else True
        if include_objective:
            parts.extend(
                [
                    f"# Objective: {self.objective.title}",
                    "",
                    "## Goals",
                ]
            )

            for goal in self.objective.goals:
                parts.append(f"- {goal}")

            parts.extend(["", "## Success Criteria"])
            for criterion in self.objective.success_criteria:
                check = "x" if criterion.completed else " "
                parts.append(f"- [{check}] {criterion.description}")

            if self.objective.constraints:
                parts.extend(["", "## Constraints"])
                for constraint in self.objective.constraints:
                    parts.append(f"- {constraint}")

            if self.objective.context:
                parts.extend(["", "## Context", self.objective.context])

        # Add working directory information
        parts.extend(
            [
                "",
                "## Working Directory",
                f"All artifacts for this objective should be saved to: `{self.teambot_dir}`",
                f"- Artifacts directory: `{self.teambot_dir / 'artifacts'}`",
                f"- Example: `{self.teambot_dir / 'artifacts' / 'feature_spec.md'}`",
            ]
        )

        # Add stage-specific instructions
        stage_meta = STAGE_METADATA.get(stage)
        if stage_meta:
            parts.extend(
                [
                    "",
                    f"## Current Stage: {stage_meta.name}",
                    stage_meta.description,
                ]
            )

            # Add required artifacts for this stage from config
            stage_config = self.stages_config.stages.get(stage)
            if stage_config and stage_config.artifacts:
                parts.extend(["", "## Required Artifacts for This Stage"])
                for artifact in stage_config.artifacts:
                    parts.append(f"- `{self.teambot_dir / 'artifacts' / artifact}`")

            # Add exit criteria from config
            if stage_config and stage_config.exit_criteria:
                parts.extend(["", "## Exit Criteria"])
                for criterion in stage_config.exit_criteria:
                    parts.append(f"- {criterion}")

        # Add stage output expectations
        stage_outputs = self._get_stage_outputs(stage)
        if stage_outputs:
            parts.extend(["", "## Expected Output"])
            parts.extend(stage_outputs)

        # Include relevant prior outputs
        if stage in self.stages_config.review_stages:
            # For review, include the work that needs review
            work_stage = self._get_work_stage_for_review(stage)
            if work_stage and work_stage in self.stage_outputs:
                parts.extend(
                    [
                        "",
                        "## Work to Review",
                        self.stage_outputs[work_stage],
                    ]
                )

        return "\n".join(parts)

    def _get_stage_outputs(self, stage: WorkflowStage) -> list[str]:
        """Get expected output description for a specific stage.

        Args:
            stage: The workflow stage

        Returns:
            List of output expectations based on stage artifacts
        """
        # Get artifacts from config
        stage_config = self.stages_config.stages.get(stage)
        if stage_config and stage_config.artifacts:
            return [f"- {artifact}" for artifact in stage_config.artifacts]

        # Fallback for stages without explicit artifacts
        fallback_outputs: dict[WorkflowStage, list[str]] = {
            WorkflowStage.SETUP: [
                "- Confirmation that setup is complete",
            ],
            WorkflowStage.IMPLEMENTATION: [
                "- Implemented code and tests per the plan",
            ],
        }
        return fallback_outputs.get(stage, [])

    def _load_prompt_template(self, stage_config: Any) -> str | None:
        """Load prompt template content from file if specified.

        Args:
            stage_config: The stage configuration containing prompt_template path

        Returns:
            The prompt template content, or None if not specified or not found
        """
        if not stage_config or not stage_config.prompt_template:
            return None

        # Resolve path relative to project root (where stages.yaml lives)
        # Find project root by looking for common markers
        project_root = self.teambot_dir.parent  # .teambot parent is project root
        if self.stages_config.source != "built-in-defaults":
            # Use the directory containing stages.yaml as reference
            project_root = Path(self.stages_config.source).parent

        template_path = project_root / stage_config.prompt_template
        if template_path.exists():
            try:
                return template_path.read_text(encoding="utf-8")
            except OSError:
                return None
        return None

    def _get_work_stage_for_review(self, review_stage: WorkflowStage) -> WorkflowStage | None:
        """Get the work stage that corresponds to a review stage."""
        for work_stage, review in self.stages_config.work_to_review_mapping.items():
            if review == review_stage:
                return work_stage
        return None

    def _get_next_stage(self, current: WorkflowStage) -> WorkflowStage:
        """Get the next stage in the workflow."""
        stage_order = self.stages_config.stage_order
        try:
            idx = stage_order.index(current)
            if idx + 1 < len(stage_order):
                return stage_order[idx + 1]
        except ValueError:
            pass
        return WorkflowStage.COMPLETE

    def _save_state(self, result: ExecutionResult | None = None) -> None:
        """Save orchestration state to workflow state file.

        Args:
            result: The execution result that caused this save. If None,
                    status is inferred from self.cancelled.
        """
        state_file = self.teambot_dir / "orchestration_state.json"

        import json

        # Determine status from execution result
        if result is not None:
            status = result.value
        elif self.cancelled:
            status = "cancelled"
        elif self.current_stage == WorkflowStage.COMPLETE:
            status = "complete"
        else:
            status = "in_progress"

        state = {
            "objective_file": str(self.objective_path),
            "current_stage": self.current_stage.name,
            "elapsed_seconds": self.time_manager.elapsed_seconds,
            "max_seconds": self.time_manager.max_seconds,
            "status": status,
            "stages_config_source": self.stages_config.source,
            "feature_name": self.feature_name,
            "acceptance_tests_passed": self.acceptance_tests_passed,
            "acceptance_test_iterations": self.acceptance_test_iterations,
            "acceptance_test_history": self._acceptance_test_history,
            "acceptance_test_summary": (
                self.acceptance_test_result.summary if self.acceptance_test_result else None
            ),
            "stage_outputs": {k.name: v for k, v in self.stage_outputs.items()},
            "parallel_group_status": self.parallel_group_status,
        }

        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    @classmethod
    def resume(cls, teambot_dir: Path, config: dict[str, Any]) -> ExecutionLoop:
        """Resume from saved state.

        Args:
            teambot_dir: Either the root teambot directory (.teambot/) or a
                        feature-specific subdirectory (.teambot/user-auth/).
                        If the root is given, the most recently modified
                        orchestration_state.json across subdirectories is used.
            config: TeamBot configuration dict.

        Returns:
            ExecutionLoop ready to continue execution
        """
        import json

        state_file = teambot_dir / "orchestration_state.json"

        # If not found directly, scan subdirectories for state files
        if not state_file.exists():
            state_file = cls._find_latest_state_file(teambot_dir)

        if state_file is None or not state_file.exists():
            raise ValueError("No orchestration state to resume")

        state = json.loads(state_file.read_text(encoding="utf-8"))

        objective_path = Path(state["objective_file"])

        # Get the parent teambot dir (feature dir's parent)
        # since __init__ will append the feature name again
        feature_dir = state_file.parent
        parent_teambot_dir = feature_dir.parent

        loop = cls(
            objective_path=objective_path,
            config=config,
            teambot_dir=parent_teambot_dir,
            max_hours=state["max_seconds"] / 3600,
        )

        loop.time_manager.resume(state["elapsed_seconds"])
        loop.current_stage = WorkflowStage[state["current_stage"]]

        # Restore stage outputs
        for stage_name, output in state.get("stage_outputs", {}).items():
            loop.stage_outputs[WorkflowStage[stage_name]] = output

        # Restore acceptance test state
        loop.acceptance_tests_passed = state.get("acceptance_tests_passed", False)
        loop.acceptance_test_iterations = state.get("acceptance_test_iterations", 0)
        loop._acceptance_test_history = state.get("acceptance_test_history", [])

        # Restore parallel group status (with backward compatibility for old state files)
        loop.parallel_group_status = state.get("parallel_group_status", {})

        return loop

    @staticmethod
    def _find_latest_state_file(teambot_dir: Path) -> Path | None:
        """Find the most recently modified orchestration_state.json in subdirs.

        Args:
            teambot_dir: Root teambot directory to scan.

        Returns:
            Path to the newest state file, or None if none found.
        """
        candidates = list(teambot_dir.glob("*/orchestration_state.json"))
        if not candidates:
            return None
        # Return the most recently modified state file
        return max(candidates, key=lambda p: p.stat().st_mtime)
