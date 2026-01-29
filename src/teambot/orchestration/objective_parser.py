"""Objective file parser for extracting goals and criteria."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SuccessCriterion:
    """A success criterion with completion status."""

    description: str
    completed: bool = False


@dataclass
class ParsedObjective:
    """Structured representation of an objective file."""

    title: str
    goals: list[str] = field(default_factory=list)
    success_criteria: list[SuccessCriterion] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    context: str | None = None
    raw_content: str = ""


def parse_objective_file(path: Path) -> ParsedObjective:
    """Parse a markdown objective file.

    Args:
        path: Path to the objective markdown file

    Returns:
        ParsedObjective with extracted structure

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Objective file not found: {path}")

    content = path.read_text()
    sections = _extract_sections(content)

    return ParsedObjective(
        title=_extract_title(content),
        goals=_parse_list_section(sections.get("Goals", "")),
        success_criteria=_parse_criteria_section(sections.get("Success Criteria", "")),
        constraints=_parse_list_section(sections.get("Constraints", "")),
        context=sections.get("Context"),
        raw_content=content,
    )


def _extract_title(content: str) -> str:
    """Extract title from H1 heading."""
    match = re.search(r"^#\s+(?:Objective:\s*)?(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


def _extract_sections(content: str) -> dict[str, str]:
    """Extract sections by ## headers."""
    sections: dict[str, str] = {}
    pattern = r"^##\s+(.+?)$"
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    for i, match in enumerate(matches):
        header = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()
        if section_content:
            sections[header] = section_content

    return sections


def _parse_list_section(content: str) -> list[str]:
    """Parse numbered or bulleted list."""
    items = []
    for line in content.split("\n"):
        # Match "1. text" or "- text" or "* text"
        match = re.match(r"^\s*(?:\d+\.|[-*])\s+(.+)$", line)
        if match:
            items.append(match.group(1).strip())
    return items


def _parse_criteria_section(content: str) -> list[SuccessCriterion]:
    """Parse success criteria with checkbox status."""
    criteria = []
    for line in content.split("\n"):
        # Match "- [ ] text" or "- [x] text"
        match = re.match(r"^\s*-\s+\[([ xX])\]\s+(.+)$", line)
        if match:
            completed = match.group(1).lower() == "x"
            description = match.group(2).strip()
            criteria.append(SuccessCriterion(description=description, completed=completed))
    return criteria
