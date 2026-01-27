"""History file manager for creating and managing agent action history."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from teambot.history.frontmatter import (
    HistoryMetadata,
    create_history_content,
    parse_frontmatter,
    scan_frontmatter_only,
)


def generate_history_filename(metadata: HistoryMetadata) -> str:
    """Generate filename from metadata in YYYY-MM-DD-HHMMSS-<action-type>.md format."""
    ts = metadata.timestamp
    date_part = ts.strftime("%Y-%m-%d-%H%M%S")
    action_part = metadata.action_type.replace(" ", "-").lower()
    return f"{date_part}-{action_part}.md"


class HistoryFileManager:
    """Manages history files with frontmatter metadata."""

    def __init__(self, teambot_dir: Path):
        self.teambot_dir = teambot_dir
        self.history_dir = teambot_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def create_history_file(self, metadata: HistoryMetadata, content: str) -> Path:
        """Create a new history file with frontmatter and content."""
        filename = generate_history_filename(metadata)
        filepath = self.history_dir / filename

        full_content = create_history_content(metadata, content)
        filepath.write_text(full_content, encoding="utf-8")

        return filepath

    def scan_history_files(self) -> list[Path]:
        """Scan directory for all history files."""
        return sorted(self.history_dir.glob("*.md"))

    def scan_all_frontmatter(self) -> list[dict[str, Any]]:
        """Scan all history files and return their frontmatter metadata."""
        results = []
        for filepath in self.scan_history_files():
            metadata = scan_frontmatter_only(filepath)
            results.append({"metadata": metadata, "path": filepath})
        return results

    def load_history_file(self, filepath: Path) -> tuple[dict[str, Any], str]:
        """Load a complete history file with metadata and content."""
        return parse_frontmatter(filepath)

    def get_recent_files(self, limit: int = 10) -> list[Path]:
        """Get most recent N history files (sorted by filename descending)."""
        files = self.scan_history_files()
        # Sort by filename descending (most recent first since filename has timestamp)
        return sorted(files, reverse=True)[:limit]

    def filter_by_agent(self, agent_id: str) -> list[dict[str, Any]]:
        """Filter history files by agent ID."""
        results = []
        for item in self.scan_all_frontmatter():
            if item["metadata"].get("agent_id") == agent_id:
                results.append(item)
        return results
