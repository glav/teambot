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
            self.stages_config = load_stages_config(
                Path(stages_path) if stages_path else None
            )

        # Current state
        self.current_stage = WorkflowStage.SETUP
        self.stage_outputs: dict[WorkflowStage, str] = {}

        # Acceptance test tracking
        self.acceptance_tests_passed: bool = False
        self.acceptance_test_result: AcceptanceTestResult | None = None
        self.acceptance_test_iterations: int = 0

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

        try:
            while self.current_stage != WorkflowStage.COMPLETE:
                # Check cancellation
                if self.cancelled:
                    self._save_state(ExecutionResult.CANCELLED)
                    return ExecutionResult.CANCELLED

                # Check timeout
                if self.time_manager.is_expired():
                    self._save_state(ExecutionResult.TIMEOUT)
                    return ExecutionResult.TIMEOUT

                stage = self.current_stage

                if on_progress:
                    on_progress("stage_changed", {"stage": stage.name})

                # Execute stage based on type
                stage_config = self.stages_config.stages.get(stage)

                if stage in self.stages_config.acceptance_test_stages:
                    # Execute acceptance test stage with retry loop
                    result = await self._execute_acceptance_test_with_retry(
                        stage, on_progress
                    )
                    if not self.acceptance_tests_passed:
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
                        self._save_state(ExecutionResult.ACCEPTANCE_TEST_FAILED)
                        return ExecutionResult.ACCEPTANCE_TEST_FAILED

                    result = await self._execute_review_stage(stage, on_progress)
                    if result == ReviewStatus.FAILED:
                        self._save_state(ExecutionResult.REVIEW_FAILED)
                        return ExecutionResult.REVIEW_FAILED
                else:
                    await self._execute_work_stage(stage, on_progress)

                # Advance to next stage
                self.current_stage = self._get_next_stage(stage)

                # Save state after each stage completion for resumability
                self._save_state()

            self._save_state(ExecutionResult.COMPLETE)
            return ExecutionResult.COMPLETE

        except Exception:
            self._save_state(ExecutionResult.ERROR)
            raise

    def cancel(self) -> None:
        """Request cancellation of execution."""
        self.cancelled = True

    async def _execute_acceptance_test_stage(
        self,
        stage: WorkflowStage,
        on_progress: Callable[[str, Any], None] | None,
    ) -> AcceptanceTestResult:
        """Execute acceptance test stage.

        This stage:
        1. Finds the feature spec (from artifacts or docs/feature-specs/)
        2. Parses acceptance test scenarios from the spec
        3. Executes each scenario against the SDK client
        4. Reports results and blocks if any fail
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
                "ERROR: Could not find feature specification to extract "
                "acceptance test scenarios."
            )
            return self.acceptance_test_result

        # Create executor and run tests
        executor = AcceptanceTestExecutor(
            spec_content=spec_content,
            timeout=60.0,
            on_progress=on_progress,
        )

        executor.load_scenarios()

        if not executor.scenarios:
            # No acceptance tests defined - this is a warning but not a failure
            self.acceptance_test_result = AcceptanceTestResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                scenarios=[],
            )
            self.stage_outputs[stage] = (
                "WARNING: No acceptance test scenarios found in the feature spec. "
                "Acceptance test validation skipped."
            )
            self.acceptance_tests_passed = True  # Allow to proceed with warning
            return self.acceptance_test_result

        # Execute acceptance tests
        self.acceptance_test_result = await executor.execute_all(self.sdk_client)

        # Generate report
        report = generate_acceptance_test_report(self.acceptance_test_result)
        self.stage_outputs[stage] = report

        # Save report to artifacts
        report_path = self.teambot_dir / "artifacts" / "acceptance_test_results.md"
        report_path.write_text(report)

        # Update tracking
        self.acceptance_tests_passed = self.acceptance_test_result.all_passed

        if on_progress:
            on_progress("acceptance_test_stage_complete", {
                "stage": stage.name,
                "passed": self.acceptance_test_result.passed,
                "failed": self.acceptance_test_result.failed,
                "all_passed": self.acceptance_tests_passed,
            })

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

        while self.acceptance_test_iterations < max_iterations:
            self.acceptance_test_iterations += 1

            if on_progress:
                on_progress("acceptance_test_iteration", {
                    "iteration": self.acceptance_test_iterations,
                    "max_iterations": max_iterations,
                })

            # Run acceptance tests
            result = await self._execute_acceptance_test_stage(stage, on_progress)

            if result.all_passed:
                # Tests passed - we're done
                self.acceptance_tests_passed = True
                return result

            # Tests failed - if we have iterations left, try to fix
            if self.acceptance_test_iterations >= max_iterations:
                # No more iterations - fail
                if on_progress:
                    on_progress("acceptance_test_max_iterations_reached", {
                        "iterations_used": self.acceptance_test_iterations,
                    })
                break

            # Build context for fix
            fix_context = self._build_acceptance_test_fix_context(result)

            if on_progress:
                on_progress("acceptance_test_fix_start", {
                    "iteration": self.acceptance_test_iterations,
                    "failed_count": result.failed,
                })

            # Ask builder to implement fix
            fix_output = await self._execute_acceptance_test_fix(fix_context, on_progress)

            # Accumulate fix outputs for traceability
            fix_record = (
                f"## Iteration {self.acceptance_test_iterations} Fix Attempt\n\n"
                f"{fix_output}\n\n"
                f"---\n\n"
            )
            if stage in self.stage_outputs:
                self.stage_outputs[stage] += fix_record
            else:
                self.stage_outputs[stage] = fix_record

            if on_progress:
                on_progress("acceptance_test_fix_complete", {
                    "iteration": self.acceptance_test_iterations,
                })

        # All iterations exhausted - tests still failing
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
        parts = [
            "# Acceptance Test Fix Required",
            "",
            "The acceptance tests have **FAILED**. Your task is to analyze the failures "
            "and implement a fix to make the tests pass.",
            "",
            "## Failed Test Results",
            "",
            generate_acceptance_test_report(test_result),
            "",
            "## Feature Specification",
            "",
        ]

        # Include feature spec
        spec_content = self._find_feature_spec_content()
        if spec_content:
            parts.append(spec_content)
        else:
            parts.append("(Feature spec not found)")

        parts.extend([
            "",
            "## Your Task",
            "",
            "1. Analyze the failed acceptance tests above",
            "2. Identify the root cause of each failure",
            "3. Review the current implementation code",
            "4. Make the necessary code changes to fix the failures",
            "5. Ensure the changes don't break existing functionality",
            "",
            "Focus on making the acceptance tests pass. The tests validate "
            "real user-facing functionality, so the fixes must address the "
            "actual behavior, not just test expectations.",
            "",
            "## Previous Stage Outputs",
            "",
        ])

        # Include relevant prior stage outputs
        for output_stage in [
            WorkflowStage.IMPLEMENTATION,
            WorkflowStage.TEST,
            WorkflowStage.PLAN,
        ]:
            if output_stage in self.stage_outputs:
                parts.extend([
                    f"### {output_stage.name}",
                    "",
                    self.stage_outputs[output_stage][:2000],  # Truncate for context
                    "",
                ])

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
            return artifacts_spec.read_text()

        # Check docs/feature-specs/
        feature_specs_dir = self.teambot_dir.parent.parent / "docs" / "feature-specs"
        if feature_specs_dir.exists():
            for spec_file in feature_specs_dir.glob("*.md"):
                # Simple matching - could be improved
                if self.feature_name.replace("-", "") in spec_file.stem.replace("-", ""):
                    return spec_file.read_text()

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
            parts.extend([
                f"# Objective: {self.objective.title}",
                "",
                "## Goals",
            ])

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
        parts.extend([
            "",
            "## Working Directory",
            f"All artifacts for this objective should be saved to: `{self.teambot_dir}`",
            f"- Artifacts directory: `{self.teambot_dir / 'artifacts'}`",
            f"- Example: `{self.teambot_dir / 'artifacts' / 'feature_spec.md'}`",
        ])

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
                return template_path.read_text()
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
            "acceptance_test_summary": (
                self.acceptance_test_result.summary
                if self.acceptance_test_result
                else None
            ),
            "stage_outputs": {k.name: v for k, v in self.stage_outputs.items()},
        }

        state_file.write_text(json.dumps(state, indent=2))

    @classmethod
    def resume(cls, teambot_dir: Path, config: dict[str, Any]) -> ExecutionLoop:
        """Resume from saved state.

        Args:
            teambot_dir: The feature-specific teambot directory containing
                        orchestration_state.json (e.g., .teambot/user-auth/)

        Returns:
            ExecutionLoop ready to continue execution
        """
        import json

        state_file = teambot_dir / "orchestration_state.json"

        if not state_file.exists():
            raise ValueError("No orchestration state to resume")

        state = json.loads(state_file.read_text())

        objective_path = Path(state["objective_file"])

        # Get the parent teambot dir (feature dir's parent)
        # since __init__ will append the feature name again
        parent_teambot_dir = teambot_dir.parent

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

        return loop
