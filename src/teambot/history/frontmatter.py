"""Frontmatter parsing utilities for history files."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import yaml


@dataclass
class HistoryMetadata:
    """Structured frontmatter for history files."""

    title: str
    description: str
    timestamp: datetime
    agent_id: str
    action_type: str
    files_affected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "files_affected": self.files_affected,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryMetadata:
        """Deserialize metadata from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            timestamp=timestamp,
            agent_id=data.get("agent_id", ""),
            action_type=data.get("action_type", ""),
            files_affected=data.get("files_affected", []),
        )


def parse_frontmatter(file_path: Path) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown file."""
    try:
        post = frontmatter.load(file_path)
        return dict(post.metadata), post.content
    except Exception:
        # If parsing fails, return empty metadata and full content
        content = file_path.read_text(encoding="utf-8")
        return {}, content


def scan_frontmatter_only(file_path: Path) -> dict[str, Any]:
    """Quickly scan only the frontmatter without loading full content."""
    with open(file_path, encoding="utf-8") as f:
        # Check for frontmatter delimiter
        first_line = f.readline()
        if first_line.strip() != "---":
            return {}

        # Read until closing delimiter
        yaml_lines = []
        for line in f:
            if line.strip() == "---":
                break
            yaml_lines.append(line)

        if yaml_lines:
            try:
                return yaml.safe_load("".join(yaml_lines)) or {}
            except yaml.YAMLError:
                return {}
    return {}


def create_frontmatter(metadata: HistoryMetadata) -> str:
    """Create YAML frontmatter string from metadata."""
    data = metadata.to_dict()
    yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_content}---\n"


def create_history_content(metadata: HistoryMetadata, body: str) -> str:
    """Create complete history file with frontmatter and body."""
    fm = create_frontmatter(metadata)
    return f"{fm}\n{body}"
