"""SDD prompt file synchronization and validation.

This module provides functions for:
- Incrementally syncing SDD prompt files during `teambot init`
- Validating prompt file references before workflow execution
- Detecting orphaned prompt files not referenced by any stage
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from teambot.scaffolds import get_scaffolds_dir

if TYPE_CHECKING:
    from teambot.orchestration.stage_config import StagesConfiguration


class SyncResult(NamedTuple):
    """Result of a prompt file sync operation.

    Attributes:
        filename: Name of the prompt file (e.g., 'sdd.0-initialize.prompt.md')
        target: Full path to target file location
        copied: True if file was copied, False if skipped
        reason: Explanation - 'copied', 'skipped_exists', or 'source_missing'
    """

    filename: str
    target: Path
    copied: bool
    reason: str


@dataclass
class ValidationResult:
    """Result of prompt file validation.

    Attributes:
        valid: True if all referenced prompt files exist
        missing: List of (path, stage_name) tuples for missing files
        orphaned: List of file paths not referenced by any stage
    """

    valid: bool
    missing: list[tuple[str, str]]
    orphaned: list[str]


class PromptValidationError(Exception):
    """Raised when prompt file validation fails.

    Contains actionable error message with remediation steps.
    """

    def __init__(
        self,
        missing: list[tuple[str, str]],
        invalid: list[tuple[str, str]] | None = None,
    ):
        self.missing = missing
        self.invalid = invalid or []
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        lines = []
        if self.invalid:
            lines.append("Invalid prompt_template configuration in stages.yaml:")
            for description, stage in self.invalid:
                lines.append(f"  - {description} (stage: {stage})")
            lines.append("")
        if self.missing:
            lines.append("Missing prompt file(s) referenced in stages.yaml:")
            for path, stage in self.missing:
                lines.append(f"  - {path} (stage: {stage})")
            lines.append("")
            lines.append("Run 'teambot init' to sync missing SDD prompt files.")
        return "\n".join(lines)


def get_sdd_prompt_dir() -> Path:
    """Get path to bundled SDD prompt files."""
    return get_scaffolds_dir() / ".agent" / "commands" / "sdd"


def sync_sdd_prompts(
    target_root: Path,
    *,
    force: bool = False,
) -> list[SyncResult]:
    """Sync SDD prompt files from scaffolds to target directory.

    Only syncs files matching 'sdd.*.prompt.md' pattern.
    Existing files are preserved unless force=True.

    Args:
        target_root: Root directory of user's repository
        force: If True, overwrite existing files

    Returns:
        List of SyncResult for each prompt file processed
    """
    results: list[SyncResult] = []

    scaffold_dir = get_sdd_prompt_dir()
    target_dir = target_root / ".agent" / "commands" / "sdd"

    if not scaffold_dir.exists():
        return results

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Sync each SDD prompt file (sorted for predictable output)
    for scaffold_file in sorted(scaffold_dir.glob("sdd.*.prompt.md")):
        target_file = target_dir / scaffold_file.name

        if target_file.exists() and not force:
            results.append(SyncResult(scaffold_file.name, target_file, False, "skipped_exists"))
        else:
            shutil.copy2(scaffold_file, target_file)
            results.append(SyncResult(scaffold_file.name, target_file, True, "copied"))

    return results


def validate_prompt_files(
    project_root: Path,
    stages_config: StagesConfiguration | None = None,
) -> ValidationResult:
    """Validate all prompt_template paths in stages.yaml exist.

    Args:
        project_root: Root directory containing stages.yaml
        stages_config: Pre-loaded stages configuration, or None to load

    Returns:
        ValidationResult with validation status and details

    Raises:
        PromptValidationError: If any referenced prompt files are missing
    """
    from teambot.orchestration.stage_config import load_stages_config

    stages_yaml = project_root / "stages.yaml"
    if not stages_yaml.exists():
        return ValidationResult(valid=True, missing=[], orphaned=[])

    if stages_config is None:
        stages_config = load_stages_config(stages_yaml)

    missing: list[tuple[str, str]] = []
    invalid: list[tuple[str, str]] = []

    for stage, config in stages_config.stages.items():
        if config.prompt_template:
            if not isinstance(config.prompt_template, str):
                type_name = type(config.prompt_template).__name__
                invalid.append(
                    (f"Invalid prompt_template type '{type_name}' (expected str)", stage.name)
                )
                continue
            template_path = (project_root / config.prompt_template).resolve()
            # Reject paths that escape the project root (path traversal protection)
            try:
                template_path.relative_to(project_root.resolve())
            except ValueError:
                invalid.append(
                    (f"Path escapes project root: '{config.prompt_template}'", stage.name)
                )
                continue
            if not template_path.exists():
                missing.append((config.prompt_template, stage.name))

    if invalid or missing:
        raise PromptValidationError(missing, invalid)

    return ValidationResult(valid=True, missing=[], orphaned=[])


def detect_orphaned_prompts(
    project_root: Path,
    stages_config: StagesConfiguration | None = None,
) -> list[str]:
    """Find SDD prompt files not referenced by any stage.

    Args:
        project_root: Root directory containing stages.yaml
        stages_config: Pre-loaded stages configuration, or None to load

    Returns:
        List of file paths (relative to project_root) for orphaned prompt files
    """
    from teambot.orchestration.stage_config import load_stages_config

    stages_yaml = project_root / "stages.yaml"
    if not stages_yaml.exists():
        return []

    if stages_config is None:
        stages_config = load_stages_config(stages_yaml)

    # Get all referenced prompts (normalized to forward-slash, no leading ./)
    referenced = {
        Path(config.prompt_template).as_posix()
        for config in stages_config.stages.values()
        if config.prompt_template and isinstance(config.prompt_template, str)
    }

    # Get all SDD prompt files
    sdd_dir = project_root / ".agent" / "commands" / "sdd"
    if not sdd_dir.exists():
        return []

    orphaned = []
    for prompt_file in sdd_dir.glob("sdd.*.prompt.md"):
        relative_path = Path(".agent/commands/sdd") / prompt_file.name
        if relative_path.as_posix() not in referenced:
            orphaned.append(relative_path.as_posix())

    return sorted(orphaned)
