"""Parallel execution for builder agents."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentTask:
    """A task to be executed by an agent."""

    agent_id: str
    prompt: str
    description: str = ""


@dataclass
class TaskResult:
    """Result of agent task execution."""

    success: bool
    output: str = ""
    error: str | None = None


class ParallelExecutor:
    """Execute multiple agent tasks in parallel."""

    def __init__(self, sdk_client: Any, max_concurrent: int = 2):
        self.sdk_client = sdk_client
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_parallel(
        self,
        tasks: list[AgentTask],
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict[str, TaskResult]:
        """Execute tasks in parallel with concurrency limit.

        Args:
            tasks: List of agent tasks to execute
            on_progress: Callback(event_type, data) matching ExecutionLoop pattern

        Returns:
            Dict mapping agent_id to TaskResult
        """
        if not tasks:
            return {}

        async def execute_one(task: AgentTask) -> tuple[str, TaskResult]:
            async with self.semaphore:
                if on_progress:
                    on_progress(
                        "agent_running", {"agent_id": task.agent_id, "task": task.description}
                    )

                try:
                    chunks: list[str] = []

                    def on_chunk(chunk: str) -> None:
                        chunks.append(chunk)
                        if on_progress:
                            on_progress(
                                "agent_streaming", {"agent_id": task.agent_id, "chunk": chunk}
                            )

                    output = await self.sdk_client.execute_streaming(
                        task.agent_id, task.prompt, on_chunk
                    )

                    if on_progress:
                        on_progress("agent_complete", {"agent_id": task.agent_id})

                    return (task.agent_id, TaskResult(success=True, output=output))

                except asyncio.CancelledError:
                    if on_progress:
                        on_progress("agent_cancelled", {"agent_id": task.agent_id})
                    raise

                except Exception as e:
                    if on_progress:
                        on_progress("agent_failed", {"agent_id": task.agent_id, "error": str(e)})
                    return (task.agent_id, TaskResult(success=False, error=str(e)))

        results = await asyncio.gather(*[execute_one(t) for t in tasks], return_exceptions=True)

        # Convert to dict, handling exceptions
        output: dict[str, TaskResult] = {}
        for result in results:
            if isinstance(result, asyncio.CancelledError):
                # Re-raise CancelledError so caller can handle cancellation
                raise result
            if isinstance(result, Exception):
                continue
            agent_id, task_result = result
            output[agent_id] = task_result

        return output


def partition_tasks(tasks: list[str], agents: list[str] | None = None) -> list[AgentTask]:
    """Partition tasks among builder agents.

    Strategy: Round-robin assignment.

    Args:
        tasks: List of task descriptions
        agents: Agent IDs to distribute to

    Returns:
        List of AgentTask with assignments
    """
    if agents is None:
        agents = ["builder-1", "builder-2"]
    result = []
    for i, task in enumerate(tasks):
        agent = agents[i % len(agents)]
        result.append(
            AgentTask(
                agent_id=agent,
                prompt=task,
                description=task[:50] + "..." if len(task) > 50 else task,
            )
        )
    return result
