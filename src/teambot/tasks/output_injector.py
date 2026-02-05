"""Output injector for passing parent task outputs to dependent tasks."""

from teambot.tasks.formatting import format_agent_header, format_your_task_header
from teambot.tasks.models import TaskResult


class OutputInjector:
    """Injects parent task outputs into child task prompts.

    Formats parent outputs with clear headers and appends
    the child's own task prompt.
    """

    def inject(
        self,
        prompt: str,
        parent_results: dict[str, TaskResult],
        dependencies: list[str],
        agent_map: dict[str, str] | None = None,
    ) -> str:
        """Inject parent outputs into a task prompt.

        Args:
            prompt: The child task's original prompt.
            parent_results: Map of task_id -> TaskResult for parent tasks.
            dependencies: List of parent task IDs in order.
            agent_map: Optional map of task_id -> agent_id for headers.

        Returns:
            Modified prompt with parent outputs prepended.
        """
        if not dependencies:
            return prompt

        sections: list[str] = []

        for dep_id in dependencies:
            result = parent_results.get(dep_id)

            # Determine agent name for header
            if agent_map and dep_id in agent_map:
                agent_name = agent_map[dep_id]
            else:
                # Try to extract from task ID (e.g., "task-pm-1" -> "pm")
                agent_name = self._extract_agent_from_task_id(dep_id)

            if result is None:
                # Parent result missing
                header = self._format_header(agent_name, dep_id)
                sections.append(
                    f"{header}\n[Output not available - task result missing]\n"
                )
            elif not result.success:
                # Parent failed
                error_msg = result.error or "Unknown error"
                header = self._format_header(agent_name, dep_id)
                sections.append(f"{header}\n[Task failed: {error_msg}]\n")
            else:
                # Parent succeeded
                header = self._format_header(agent_name, dep_id)
                sections.append(f"{header}\n{result.output}\n")

        # Add the task's own prompt with distinct styling
        your_task_header = self._format_your_task_header()
        sections.append(f"{your_task_header}\n{prompt}")

        return "\n".join(sections)

    def _extract_agent_from_task_id(self, task_id: str) -> str:
        """Try to extract agent ID from task ID.

        Args:
            task_id: Task identifier.

        Returns:
            Extracted agent ID or the task_id itself.
        """
        # Common patterns:
        # "task-pm-1" -> "pm"
        # "t1" -> "t1" (can't extract)
        # "pm" -> "pm"

        parts = task_id.split("-")
        if len(parts) >= 2:
            # Skip "task" prefix if present
            if parts[0] == "task" and len(parts) >= 2:
                return parts[1]
            return parts[0]

        return task_id

    def _format_header(self, agent_name: str, task_id: str) -> str:
        """Format a styled header for agent output.

        Args:
            agent_name: The agent identifier (e.g., 'pm', 'builder-1').
            task_id: The task identifier.

        Returns:
            Formatted header string with color markup, icon, and delimiter.
        """
        return format_agent_header(agent_name, task_id)

    def _format_your_task_header(self) -> str:
        """Format the 'Your Task' section header.

        Returns:
            Formatted header string with distinct styling.
        """
        return format_your_task_header()
