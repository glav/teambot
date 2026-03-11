"""Scaffold file management for teambot init."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import NamedTuple


@dataclass
class ConflictInfo:
    """Information about a file conflict."""

    prefix: str  # e.g., "sdd.4-"
    scaffold_name: str  # e.g., "sdd.4-task-planner-for-feature.prompt.md"
    existing_name: str  # e.g., "sdd.4-determine-test-strategy.prompt.md"


class CopyResult(NamedTuple):
    """Result of a scaffold copy operation."""

    source: str
    target: Path
    copied: bool
    reason: str  # "copied", "skipped_exists", "source_missing", "skipped_not_empty"


def extract_numbered_prefix(filename: str) -> str | None:
    """Extract numbered prefix from SDD prompt filename.

    Args:
        filename: e.g., "sdd.4-task-planner-for-feature.prompt.md"

    Returns:
        Prefix like "sdd.4-" or None if not matching pattern
    """
    match = re.match(r"^(sdd\.\d+-)", filename)
    return match.group(1) if match else None


def detect_sdd_conflicts(
    scaffold_dir: Path,
    target_dir: Path,
) -> list[ConflictInfo]:
    """Detect SDD prompt file conflicts.

    Looks for files with same numbered prefix but different names.

    Args:
        scaffold_dir: Path to scaffold root directory
        target_dir: Path to target root directory

    Returns:
        List of ConflictInfo for each detected conflict
    """
    scaffold_sdd = scaffold_dir / ".agent" / "commands" / "sdd"
    target_sdd = target_dir / ".agent" / "commands" / "sdd"

    if not scaffold_sdd.exists() or not target_sdd.exists():
        return []

    # Build prefix -> filename maps
    scaffold_prefixes: dict[str, str] = {}
    for f in scaffold_sdd.glob("sdd.*.prompt.md"):
        prefix = extract_numbered_prefix(f.name)
        if prefix:
            scaffold_prefixes[prefix] = f.name

    # Track all target filenames per prefix (multiple files may share a prefix)
    target_prefixes: dict[str, list[str]] = {}
    for f in target_sdd.glob("sdd.*.prompt.md"):
        prefix = extract_numbered_prefix(f.name)
        if prefix:
            target_prefixes.setdefault(prefix, []).append(f.name)

    # Find conflicts: same prefix, any target filename differs from scaffold name
    conflicts = []
    for prefix, scaffold_name in scaffold_prefixes.items():
        if prefix in target_prefixes:
            for existing_name in sorted(target_prefixes[prefix]):
                if scaffold_name != existing_name:
                    conflicts.append(ConflictInfo(prefix, scaffold_name, existing_name))

    return sorted(conflicts, key=lambda c: c.prefix)


def backup_directory(source: Path, backup_root: Path) -> Path:
    """Move directory to timestamped backup location.

    Args:
        source: Directory to back up (e.g., .agent/)
        backup_root: Parent for backups (e.g., .agent-tracking/backups/)

    Returns:
        Path to created backup directory

    Raises:
        FileNotFoundError: If source doesn't exist
    """
    from datetime import datetime

    if not source.exists():
        raise FileNotFoundError(f"Cannot backup: {source} does not exist")

    # Generate filesystem-safe timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_root / timestamp / source.name

    # Ensure backup parent exists
    backup_dir.parent.mkdir(parents=True, exist_ok=True)

    # Move source to backup
    shutil.move(str(source), str(backup_dir))

    return backup_dir


def get_scaffolds_dir() -> Path:
    """Get path to bundled scaffold files.

    Returns:
        Path to the scaffolds directory within the installed package.
    """
    pkg = files("teambot")
    scaffolds = pkg.joinpath("scaffolds")

    # Handle both real paths (editable install) and traversable (wheel)
    if hasattr(scaffolds, "_path"):
        return Path(scaffolds._path)
    return Path(str(scaffolds))


def copy_scaffold_file(
    scaffold_name: str,
    target_path: Path,
    *,
    force: bool = False,
) -> CopyResult:
    """Copy a single scaffold file to target location.

    Args:
        scaffold_name: Name of file within scaffolds directory
        target_path: Destination path in user's repository
        force: If True, overwrite existing files

    Returns:
        CopyResult indicating what happened
    """
    source_path = get_scaffolds_dir() / scaffold_name

    if not source_path.exists():
        return CopyResult(scaffold_name, target_path, False, "source_missing")

    if target_path.exists() and not force:
        return CopyResult(scaffold_name, target_path, False, "skipped_exists")

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_path, target_path)
    return CopyResult(scaffold_name, target_path, True, "copied")


def copy_scaffold_directory(
    scaffold_name: str,
    target_path: Path,
    *,
    force: bool = False,
) -> CopyResult:
    """Copy a scaffold directory to target location.

    Only copies if target doesn't exist or is empty.

    Args:
        scaffold_name: Name of directory within scaffolds
        target_path: Destination path in user's repository
        force: If True, overwrite existing directory

    Returns:
        CopyResult indicating what happened
    """
    source_path = get_scaffolds_dir() / scaffold_name

    if not source_path.exists():
        return CopyResult(scaffold_name, target_path, False, "source_missing")

    # Check if target exists and is non-empty
    if target_path.exists():
        if not force:
            # Check if directory is empty
            if any(target_path.iterdir()):
                return CopyResult(scaffold_name, target_path, False, "skipped_not_empty")
            # Empty directory - remove it so copytree works
            target_path.rmdir()

    # Force mode: remove existing directory
    if target_path.exists() and force:
        shutil.rmtree(target_path)

    # Ensure parent exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(source_path, target_path)
    return CopyResult(scaffold_name, target_path, True, "copied")


def copy_all_scaffolds(
    target_root: Path,
    *,
    force: bool = False,
) -> list[CopyResult]:
    """Copy all scaffold files to target repository.

    Args:
        target_root: Root directory of user's repository
        force: If True, overwrite existing files

    Returns:
        List of CopyResult for each scaffold item
    """
    results = []

    # Single files
    results.append(
        copy_scaffold_file(
            "stages.yaml",
            target_root / "stages.yaml",
            force=force,
        )
    )

    results.append(
        copy_scaffold_file(
            "AGENTS.md",
            target_root / "AGENTS.md",
            force=force,
        )
    )

    results.append(
        copy_scaffold_file(
            "sdd-objective-template.md",
            target_root / "docs" / "sdd-objective-template.md",
            force=force,
        )
    )

    # Directories
    results.append(
        copy_scaffold_directory(
            "agents",
            target_root / ".github" / "agents",
            force=force,
        )
    )

    results.append(
        copy_scaffold_directory(
            ".agent",
            target_root / ".agent",
            force=force,
        )
    )

    return results
