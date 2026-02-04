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
    final_output: str | None = None
    summary: str | None = None
    suggestions: list[str] = field(default_factory=list)
    report_path: Path | None = None


class ReviewIterator:
    """Manages review→feedback→action cycles with strict verification."""

    MAX_ITERATIONS = 4

    def __init__(self, sdk_client: Any, teambot_dir: Path):
        self.sdk_client = sdk_client
        self.teambot_dir = teambot_dir
        self.repo_root = self._find_repo_root()

    def _find_repo_root(self) -> Path | None:
        """Find the git repository root."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def _gather_evidence(self) -> str:
        """Gather actual evidence of changes for review verification.

        Returns:
            String containing git diff, modified files, and recent test results.
        """
        import subprocess

        evidence_parts = []

        if not self.repo_root:
            return "(Unable to gather evidence - not in git repository)"

        # Get git diff (staged and unstaged changes)
        try:
            diff_result = subprocess.run(
                ["git", "diff", "HEAD", "--stat"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=10,
            )
            if diff_result.returncode == 0 and diff_result.stdout.strip():
                evidence_parts.append("## Git Changes (Summary)")
                evidence_parts.append("```")
                evidence_parts.append(diff_result.stdout.strip()[:2000])
                evidence_parts.append("```")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Get list of modified files
        try:
            status_result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=5,
            )
            if status_result.returncode == 0 and status_result.stdout.strip():
                evidence_parts.append("\n## Modified Files")
                evidence_parts.append("```")
                evidence_parts.append(status_result.stdout.strip()[:1000])
                evidence_parts.append("```")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Check for recent test results in artifacts
        test_results_path = self.teambot_dir / "artifacts" / "test_results.md"
        if test_results_path.exists():
            try:
                content = test_results_path.read_text()[:1500]
                evidence_parts.append("\n## Recent Test Results")
                evidence_parts.append(content)
            except OSError:
                pass

        if not evidence_parts:
            return "(No evidence of changes found)"

        return "\n".join(evidence_parts)

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

                # Gather evidence of actual changes for strict review
                evidence = self._gather_evidence()

                # Execute review with evidence
                review_output, approved, feedback = await self._execute_review(
                    review_agent, work_output, evidence
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
                        final_output=review_output,
                    )

                # Incorporate feedback for next iteration
                current_context = self._incorporate_feedback(current_context, feedback, work_output)

            except asyncio.CancelledError:
                # Get last review output if available
                last_output = iteration_history[-1].review_output if iteration_history else None
                return ReviewResult(
                    status=ReviewStatus.CANCELLED,
                    iterations_used=iteration,
                    final_output=last_output,
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
        evidence: str = "",
    ) -> tuple[str, bool, str | None]:
        """Execute review phase and parse result.

        Args:
            agent_id: The reviewer agent ID
            work_output: The work output to review
            evidence: Actual evidence gathered (git diff, test results)

        Returns:
            Tuple of (review_output, approved, feedback)
        """
        review_prompt = self._build_strict_review_prompt(work_output, evidence)
        review_output = await self.sdk_client.execute_streaming(agent_id, review_prompt, None)

        # Parse approval from review output (strict mode)
        approved = self._parse_approval_strict(review_output)
        feedback = self._extract_feedback(review_output) if not approved else None

        return review_output, approved, feedback

    def _build_strict_review_prompt(self, work_output: str, evidence: str = "") -> str:
        """Build a strict review prompt requiring demonstrated proof.

        Args:
            work_output: The work output to review
            evidence: Actual evidence gathered from git/tests

        Returns:
            Review prompt with strict verification requirements
        """
        evidence_section = ""
        if evidence and evidence != "(No evidence of changes found)":
            evidence_section = f"""
## Actual Evidence (from git and test artifacts)

The following evidence was automatically gathered. Use this to VERIFY
the claims made in the work output:

{evidence}

"""

        return f"""# Strict Review Required

You must thoroughly review the following work output and verify it meets
requirements. You have access to ACTUAL EVIDENCE below - use it to verify claims.

## Work Output to Review

{work_output}
{evidence_section}
## Verification Checklist

Before approving, you MUST verify:

1. **Code Changes Exist**: Are there actual code changes shown (not just descriptions)?
   - Cross-reference with the "Actual Evidence" section if available
2. **Tests Included**: Are tests written AND shown to pass (actual pytest output)?
3. **Requirements Met**: Does the work address the original requirements?
4. **No Placeholders**: Are there any TODO, FIXME, or placeholder comments?
5. **Completeness**: Is the implementation complete, not partial?
6. **Evidence Matches Claims**: Do the actual git changes match what was claimed?

## Review Output Format

You MUST use one of these exact formats:

### If APPROVING (all criteria met):
```
VERIFIED_APPROVED: [reason]

Verification Evidence:
- Code changes: [describe what was changed]
- Tests: [describe test results seen]
- Requirements: [how each requirement is met]
- Evidence check: [confirm evidence matches claims]
```

### If REJECTING (any criteria not met):
```
REJECTED: [specific reason]

Issues Found:
1. [specific issue]
2. [specific issue]

Required Actions:
1. [what must be done]
2. [what must be done]
```

## CRITICAL RULES

- Do NOT approve work that only describes what should be done
- Do NOT approve if actual code changes are not shown
- Do NOT approve if tests are not demonstrated passing
- Do NOT approve if evidence doesn't match claims
- REJECT if you cannot verify the claims made in the output

Begin your review now.
"""

    def _parse_approval_strict(self, review_output: str) -> bool:
        """Parse whether review was approved using strict criteria.

        STRICT MODE: Requires explicit VERIFIED_APPROVED marker.
        Default is REJECTED if marker not found.
        """
        output_lower = review_output.lower()

        # Check for explicit verified approval marker
        if "verified_approved:" in output_lower:
            return True

        # Legacy support: explicit approved with evidence section
        if "approved:" in output_lower and "verification evidence:" in output_lower:
            return True

        # Everything else is rejected (strict default)
        return False

    def _parse_approval(self, review_output: str) -> bool:
        """Parse whether review was approved.

        Deprecated: Use _parse_approval_strict for new code.
        Kept for backward compatibility.
        """
        return self._parse_approval_strict(review_output)

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

        # Get final review output from last iteration
        final_output = history[-1].review_output if history else None

        return ReviewResult(
            status=ReviewStatus.FAILED,
            iterations_used=len(history),
            final_output=final_output,
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
