"""Context compaction for managing history file size."""

from __future__ import annotations

from enum import Enum


class ContextStatus(Enum):
    """Status of context size check."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


class CompactionLevel(Enum):
    """Level of content compaction."""

    LITTLE = "little"
    MEDIUM = "medium"
    HIGH = "high"


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation: ~4 chars per token)."""
    return len(text) // 4


class ContextCompactor:
    """Compacts history content when approaching context limits."""

    def __init__(self, max_tokens: int = 150000, warning_threshold: float = 0.8):
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold

    def check_context_size(self, content: str) -> ContextStatus:
        """Check if content is within acceptable context limits."""
        tokens = estimate_tokens(content)
        ratio = tokens / self.max_tokens

        if ratio >= 1.0:
            return ContextStatus.CRITICAL
        elif ratio >= self.warning_threshold:
            return ContextStatus.WARNING
        else:
            return ContextStatus.OK

    def compact(self, content: str, level: CompactionLevel) -> str:
        """Compact content based on specified level."""
        if level == CompactionLevel.LITTLE:
            return self._compact_little(content)
        elif level == CompactionLevel.MEDIUM:
            return self._compact_medium(content)
        else:  # HIGH
            return self._compact_high(content)

    def _compact_little(self, content: str) -> str:
        """Light compaction - remove verbose sections, keep structure."""
        lines = content.split("\n")
        result = []
        in_details = False

        for line in lines:
            # Skip detailed/verbose sections
            if line.strip().lower().startswith("## detail"):
                in_details = True
                continue
            elif line.startswith("## ") and in_details:
                in_details = False

            if not in_details:
                result.append(line)

        return "\n".join(result)

    def _compact_medium(self, content: str) -> str:
        """Medium compaction - keep only headers and summaries."""
        lines = content.split("\n")
        result = []
        keep_next_lines = 0

        for line in lines:
            # Keep all headers
            if line.startswith("#"):
                result.append(line)
                keep_next_lines = 2  # Keep a couple lines after headers
            elif keep_next_lines > 0:
                if line.strip():  # Only non-empty lines
                    result.append(line)
                    keep_next_lines -= 1

        return "\n".join(result)

    def _compact_high(self, content: str) -> str:
        """High compaction - minimal summary only."""
        lines = content.split("\n")
        result = []

        # Keep only top-level header and first paragraph
        found_title = False
        for line in lines:
            if line.startswith("# ") and not found_title:
                result.append(line)
                found_title = True
            elif found_title and line.strip() and not line.startswith("#"):
                result.append(line)
                break

        if not result:
            # Fallback: first 100 chars
            return content[:100] + "..." if len(content) > 100 else content

        return "\n".join(result)

    def get_compaction_recommendation(self, content: str) -> CompactionLevel | None:
        """Recommend compaction level based on content size."""
        status = self.check_context_size(content)

        if status == ContextStatus.OK:
            return None
        elif status == ContextStatus.WARNING:
            return CompactionLevel.LITTLE
        else:  # CRITICAL
            return CompactionLevel.HIGH
