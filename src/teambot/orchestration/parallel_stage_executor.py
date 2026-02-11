"""Parallel execution for workflow stages."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from teambot.workflow.stages import WorkflowStage

if TYPE_CHECKING:
    from teambot.orchestration.execution_loop import ExecutionLoop


@dataclass
class StageResult:
    """Result of stage execution in parallel group."""

    stage: WorkflowStage
    success: bool
    output: str = ""
    error: str | None = None
    review_status: Any = None  # ReviewStatus | None, but avoid import cycle


class ParallelStageExecutor:
    """Execute multiple workflow stages in parallel."""

    def __init__(self, max_concurrent: int = 2):
        """Initialize executor.

        Args:
            max_concurrent: Maximum stages to run concurrently
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_parallel(
        self,
        stages: list[WorkflowStage],
        execution_loop: ExecutionLoop,
        on_progress: Callable[[str, Any], None] | None = None,
    ) -> dict[WorkflowStage, StageResult]:
        """Execute stages concurrently.

        Each stage is executed using the ExecutionLoop's existing
        _execute_work_stage or _execute_review_stage methods.

        Failures in one stage do not cancel others - all stages
        run to completion and results are collected.

        Args:
            stages: List of stages to execute in parallel
            execution_loop: ExecutionLoop instance for stage execution
            on_progress: Optional progress callback

        Returns:
            Dict mapping each stage to its result
        """
        if not stages:
            return {}

        async def execute_one(stage: WorkflowStage) -> tuple[WorkflowStage, StageResult]:
            async with self.semaphore:
                # Get agent information for progress events
                agents = execution_loop.stages_config.get_stage_agents(stage)
                agent = agents.get("work") or agents.get("review") or "builder-1"
                
                if on_progress:
                    on_progress("parallel_stage_start", {"stage": stage.name, "agent": agent})

                try:
                    # Delegate to ExecutionLoop's existing stage execution
                    if stage in execution_loop.stages_config.review_stages:
                        status = await execution_loop._execute_review_stage(stage, on_progress)
                        # Import here to avoid cycle
                        from teambot.orchestration.review_iterator import ReviewStatus

                        success = status == ReviewStatus.APPROVED
                        return stage, StageResult(
                            stage=stage,
                            success=success,
                            output=execution_loop.stage_outputs.get(stage, ""),
                            review_status=status,
                        )
                    else:
                        output = await execution_loop._execute_work_stage(stage, on_progress)
                        return stage, StageResult(
                            stage=stage,
                            success=True,
                            output=output if output else "",
                        )

                except Exception as e:
                    if on_progress:
                        on_progress(
                            "parallel_stage_failed",
                            {
                                "stage": stage.name,
                                "agent": agent,
                                "error": str(e),
                            },
                        )
                    return stage, StageResult(
                        stage=stage,
                        success=False,
                        error=str(e),
                    )

        # Execute all stages concurrently (no early cancellation)
        results = await asyncio.gather(
            *[execute_one(s) for s in stages],
            return_exceptions=True,
        )

        # Convert to dict, handling any unexpected exceptions
        output: dict[WorkflowStage, StageResult] = {}
        for result in results:
            if isinstance(result, Exception):
                # Shouldn't happen since we catch in execute_one, but handle it
                continue
            stage, stage_result = result
            output[stage] = stage_result

            if on_progress:
                event = (
                    "parallel_stage_complete" if stage_result.success else "parallel_stage_failed"
                )
                # Get agent information for progress events
                agents = execution_loop.stages_config.get_stage_agents(stage)
                agent = agents.get("work") or agents.get("review") or "builder-1"
                on_progress(event, {"stage": stage.name, "agent": agent})

        return output
