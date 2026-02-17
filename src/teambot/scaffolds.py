"""Scaffold file management for teambot init."""

from __future__ import annotations

import shutil
from importlib.resources import files
from pathlib import Path
from typing import NamedTuple


class CopyResult(NamedTuple):
    """Result of a scaffold copy operation."""

    source: str
    target: Path
    copied: bool
    reason: str  # "copied", "skipped_exists", "source_missing", "skipped_not_empty"


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
