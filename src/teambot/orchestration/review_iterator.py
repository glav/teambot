"""Review iteration system with max 4 iterations."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from teambot.workflow.stages import WorkflowStage


class ReviewStatus(Enum):
    """Status of review iteration."""

    APPROVED = "approved"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class IterationResult:
    """Result of a single review iteration."""

    iteration: int
    work_output: str
    review_output: str
    approved: bool
    feedback: str | None = None


@dataclass
class ReviewResult:
    """Final result of review iteration process."""

    status: ReviewStatus
    iterations_used: int
    summary: str | None = None
    suggestions: list[str] = field(default_factory=list)
    report_path: Path | None = None


class ReviewIterator:
    """Manages review→feedback→action cycles."""

    MAX_ITERATIONS = 4

    def __init__(self, sdk_client: Any, teambot_dir: Path):
        self.sdk_client = sdk_client
        self.teambot_dir = teambot_dir

    async def execute(
        self,
        stage: WorkflowStage,
        work_agent: str,
        review_agent: str,
        context: str,
        on_progress: Callable[[str], None] | None = None,
    ) -> ReviewResult:
        """Execute review iteration loop.

        Args:
            stage: Current workflow stage
            work_agent: Agent ID for work tasks
            review_agent: Agent ID for review tasks
            context: Initial context/prompt
            on_progress: Optional progress callback

        Returns:
            ReviewResult with status and details
        """
        iteration_history: list[IterationResult] = []
        current_context = context

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            if on_progress:
                on_progress(f"Review iteration {iteration}/{self.MAX_ITERATIONS}")

            try:
                # Execute work
                work_output = await self._execute_work(
                    work_agent, current_context, iteration_history
                )

                # Execute review
                review_output, approved, feedback = await self._execute_review(
                    review_agent, work_output
                )

                iteration_history.append(
                    IterationResult(
                        iteration=iteration,
                        work_output=work_output,
                        review_output=review_output,
                        approved=approved,
                        feedback=feedback,
                    )
                )

                if approved:
                    return ReviewResult(
                        status=ReviewStatus.APPROVED,
                        iterations_used=iteration,
                    )

                # Incorporate feedback for next iteration
                current_context = self._incorporate_feedback(current_context, feedback, work_output)

            except asyncio.CancelledError:
                return ReviewResult(
                    status=ReviewStatus.CANCELLED,
                    iterations_used=iteration,
                )

        # Max iterations reached - generate failure report
        return self._generate_failure_result(stage, iteration_history)

    async def _execute_work(
        self,
        agent_id: str,
        context: str,
        history: list[IterationResult],
    ) -> str:
        """Execute work phase with agent."""
        return await self.sdk_client.execute_streaming(agent_id, context, None)

    async def _execute_review(
        self,
        agent_id: str,
        work_output: str,
    ) -> tuple[str, bool, str | None]:
        """Execute review phase and parse result.

        Returns:
            Tuple of (review_output, approved, feedback)
        """
        review_prompt = f"Review the following work output:\n\n{work_output}"
        review_output = await self.sdk_client.execute_streaming(agent_id, review_prompt, None)

        # Parse approval from review output
        approved = self._parse_approval(review_output)
        feedback = self._extract_feedback(review_output) if not approved else None

        return review_output, approved, feedback

    def _parse_approval(self, review_output: str) -> bool:
        """Parse whether review was approved."""
        output_lower = review_output.lower()
        # Check for explicit approval markers
        if "approved:" in output_lower or "approved!" in output_lower:
            return True
        if "rejected:" in output_lower or "rejected!" in output_lower:
            return False
        # Default to approved if no rejection marker
        return "reject" not in output_lower

    def _extract_feedback(self, review_output: str) -> str:
        """Extract feedback from review output."""
        # Remove the REJECTED: prefix if present
        feedback = re.sub(r"^(?:REJECTED|REJECTED:)\s*", "", review_output, flags=re.IGNORECASE)
        return feedback.strip()

    def _incorporate_feedback(
        self, original_context: str, feedback: str | None, prior_output: str
    ) -> str:
        """Build context incorporating prior feedback."""
        parts = [original_context]
        if prior_output:
            parts.append(f"\n\nPrevious attempt:\n{prior_output}")
        if feedback:
            parts.append(f"\n\nReviewer feedback to address:\n{feedback}")
        return "\n".join(parts)

    def _generate_failure_result(
        self, stage: WorkflowStage, history: list[IterationResult]
    ) -> ReviewResult:
        """Generate detailed failure report."""
        summary = self._summarize_failures(history)
        suggestions = self._extract_suggestions(history)
        report_path = self._save_failure_report(stage, summary, suggestions, history)

        return ReviewResult(
            status=ReviewStatus.FAILED,
            iterations_used=len(history),
            summary=summary,
            suggestions=suggestions,
            report_path=report_path,
        )

    def _summarize_failures(self, history: list[IterationResult]) -> str:
        """Create summary of all iteration failures."""
        lines = [f"Review failed after {len(history)} iterations:", ""]
        for result in history:
            lines.append(f"### Iteration {result.iteration}")
            lines.append(f"**Feedback**: {result.feedback or 'No specific feedback'}")
            lines.append("")
        return "\n".join(lines)

    def _extract_suggestions(self, history: list[IterationResult]) -> list[str]:
        """Extract actionable suggestions from review feedback."""
        suggestions = []
        for result in history:
            if result.feedback:
                # Extract bullet points or numbered items from feedback
                for line in result.feedback.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith(("-", "*", "•")):
                        suggestion = stripped.lstrip("-*• ").strip()
                        if suggestion and suggestion not in suggestions:
                            suggestions.append(suggestion)
                    elif stripped and stripped[0].isdigit():
                        # Handle "1. suggestion"
                        match = re.match(r"^\d+\.\s*(.+)$", stripped)
                        if match:
                            suggestion = match.group(1).strip()
                            if suggestion and suggestion not in suggestions:
                                suggestions.append(suggestion)
        return suggestions

    def _save_failure_report(
        self,
        stage: WorkflowStage,
        summary: str,
        suggestions: list[str],
        history: list[IterationResult],
    ) -> Path:
        """Save failure report to .teambot/failures/."""
        failures_dir = self.teambot_dir / "failures"
        failures_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-{stage.name.lower()}-review-failure.md"
        report_path = failures_dir / filename

        suggestion_lines = (
            "\n".join(f"- {s}" for s in suggestions)
            if suggestions
            else "No specific suggestions extracted."
        )

        history_sections = []
        for r in history:
            truncated = r.work_output[:500] + "..." if len(r.work_output) > 500 else r.work_output
            history_sections.append(
                f"""
### Iteration {r.iteration}

**Work Output** (truncated):
```
{truncated}
```

**Review Feedback**:
{r.feedback or "No feedback"}

**Approved**: {r.approved}
"""
            )

        content = f"""# Review Failure Report: {stage.name}

**Timestamp**: {datetime.now().isoformat()}
**Stage**: {stage.name}
**Iterations**: {len(history)}

## Summary

{summary}

## Suggestions for Resolution

{suggestion_lines}

## Full Iteration History

{"".join(history_sections)}
"""
        report_path.write_text(content)
        return report_path
