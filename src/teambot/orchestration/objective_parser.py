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
    source_filename: str = ""  # Original filename for feature name fallback

    @property
    def feature_name(self) -> str:
        """Derive a short feature name from the title, filename, or first goal.

        Returns a 1-3 word dash-separated name suitable for directory names.
        Example: "Add User Authentication with OAuth2" -> "user-authentication"

        Priority:
        1. Title (if not generic like "Objective")
        2. Source filename (e.g., "sdd-objective-shared-context.md" -> "shared-context")
        3. First goal
        4. Fallback to "feature"
        """
        # If title is meaningful, use it
        if self.title.lower() not in ("objective", "untitled", ""):
            return _derive_feature_name(self.title)

        # Try to extract from filename (e.g., "sdd-objective-shared-context.md")
        if self.source_filename:
            # Remove common prefixes like "sdd-objective-" and extension
            filename = self.source_filename.lower()
            filename = re.sub(r"^(sdd-)?objective-?", "", filename)
            filename = re.sub(r"\.md$", "", filename)
            if filename and filename not in ("", "objective"):
                name = _derive_feature_name(filename)
                if name != "feature" and len(name) > 2:
                    return name

        # Try the first goal
        if self.goals:
            name = _derive_feature_name(self.goals[0])
            if name != "feature" and len(name) > 3:
                return name

        return "feature"


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

    # Try to find goals from various formats
    goals = (
        _parse_list_section(sections.get("Goals", ""))
        or _parse_list_section(sections.get("Goal", ""))
        or _extract_inline_goals(content)
    )

    # Try to find success criteria from various formats
    success_criteria = (
        _parse_criteria_section(sections.get("Success Criteria", ""))
        or _parse_criteria_section(sections.get("Success criteria", ""))
        or _extract_inline_criteria(content)
    )

    # Try to find constraints
    constraints = (
        _parse_list_section(sections.get("Constraints", ""))
        or _parse_list_section(sections.get("Key Constraints", ""))
    )

    # Try to find context
    context = (
        sections.get("Context")
        or sections.get("Technical Context")
    )

    return ParsedObjective(
        title=_extract_title(content),
        goals=goals,
        success_criteria=success_criteria,
        constraints=constraints,
        context=context,
        raw_content=content,
        source_filename=path.name,
    )


def _extract_title(content: str) -> str:
    """Extract title from H1 or H2 heading."""
    # Try H1 first
    match = re.search(r"^#\s+(?:Objective:\s*)?(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    # Try H2 Objective
    match = re.search(r"^##\s+Objective\s*$", content, re.MULTILINE)
    if match:
        return "Objective"
    
    return "Untitled"


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


def _extract_inline_goals(content: str) -> list[str]:
    """Extract goals from inline **Goal**: format."""
    goals = []
    
    # Match **Goal**: or **Goals**: followed by text
    match = re.search(r"\*\*Goals?\*\*:\s*(.+?)(?=\n\n|\n\*\*|\Z)", content, re.DOTALL)
    if match:
        goal_text = match.group(1).strip()
        # If it's a single line, treat as one goal
        if "\n" not in goal_text:
            goals.append(goal_text)
        else:
            # Try to parse as list
            for line in goal_text.split("\n"):
                line = line.strip()
                # Match list items
                list_match = re.match(r"^(?:\d+\.|[-*])\s+(.+)$", line)
                if list_match:
                    goals.append(list_match.group(1).strip())
                elif line and not line.startswith("**"):
                    goals.append(line)
    
    return goals


def _extract_inline_criteria(content: str) -> list[SuccessCriterion]:
    """Extract success criteria from inline **Success Criteria**: format."""
    criteria = []
    
    # Match **Success Criteria**: followed by content until next section
    match = re.search(
        r"\*\*Success Criteria\*\*:\s*\n((?:[-*]\s+\[[ xX]\].+\n?)+)",
        content,
        re.MULTILINE
    )
    if match:
        criteria_text = match.group(1)
        for line in criteria_text.split("\n"):
            # Match "- [ ] text" or "- [x] text"
            checkbox_match = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.+)$", line)
            if checkbox_match:
                completed = checkbox_match.group(1).lower() == "x"
                description = checkbox_match.group(2).strip()
                criteria.append(SuccessCriterion(description=description, completed=completed))
    
    return criteria


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


# Common words to skip when deriving feature names
_SKIP_WORDS = {
    # Articles and conjunctions
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    # Modal verbs
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    # Common action verbs (generic)
    "add", "create", "implement", "build", "make", "update", "fix",
    "new", "support", "enable", "allow", "enhance", "improve", "change",
    # Personal pronouns and common sentence starters
    "i", "we", "you", "it", "this", "that", "these", "those",
    "like", "want", "so", "when", "if", "then", "also",
    # Generic tech words
    "solution", "system", "feature", "functionality", "ability",
}


def _derive_feature_name(title: str) -> str:
    """Derive a short feature name from a title.

    Takes a title like "Add User Authentication with OAuth2 Support"
    and returns "user-authentication" (1-3 meaningful words, dash-separated).

    Args:
        title: The objective title

    Returns:
        A short, dash-separated feature name suitable for directory names
    """
    if not title or title == "Untitled":
        return "feature"

    # Remove common prefixes and clean up
    cleaned = title.lower().strip()

    # Remove "objective:" prefix if present
    cleaned = re.sub(r"^objective:\s*", "", cleaned)

    # Split into words, keeping only alphanumeric
    words = re.findall(r"[a-z0-9]+", cleaned)

    # Filter out common/skip words
    meaningful = [w for w in words if w not in _SKIP_WORDS and len(w) > 1]

    # Take first 1-3 meaningful words
    if not meaningful:
        # Fallback: take first 2 words from original
        meaningful = words[:2] if words else ["feature"]

    feature_words = meaningful[:3]

    # Join with dashes
    return "-".join(feature_words)
