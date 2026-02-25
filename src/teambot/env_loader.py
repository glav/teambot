"""Environment file loading utilities for TeamBot CLI.

Provides reliable .env file loading that works with uvx invocations,
subdirectory execution, explicit path specification, and loading disablement.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from dotenv import load_dotenv


class EnvArgs(NamedTuple):
    """Parsed environment-related CLI arguments."""

    env_file: Path | None
    no_env: bool


def extract_env_args(argv: list[str] | None = None) -> tuple[EnvArgs, list[str]]:
    """Extract --env-file and --no-env from argv before argparse runs.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Tuple of (EnvArgs, cleaned_argv with env args removed)
    """
    if argv is None:
        argv = sys.argv

    env_file: Path | None = None
    no_env = False
    cleaned = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--env-file":
            if i + 1 < len(argv):
                env_file = Path(argv[i + 1])
                i += 2
                continue
            # Missing value - leave for argparse to error
            cleaned.append(arg)
            i += 1
            continue
        elif arg.startswith("--env-file="):
            env_file = Path(arg.split("=", 1)[1])
            i += 1
            continue
        elif arg == "--no-env":
            no_env = True
            i += 1
            continue
        cleaned.append(arg)
        i += 1

    return EnvArgs(env_file, no_env), cleaned


def find_git_root() -> Path | None:
    """Find the git repository root, or None if not in a repo."""
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


def find_env_files(start_dir: Path | None = None, max_depth: int = 10) -> list[Path]:
    """Find .env files from start_dir up to git root or max_depth.

    Args:
        start_dir: Starting directory (defaults to cwd)
        max_depth: Maximum parent directories to traverse

    Returns:
        List of .env file paths, ordered from nearest (cwd) to farthest (parent)
    """
    if start_dir is None:
        start_dir = Path.cwd()

    start_dir = start_dir.resolve()
    git_root = find_git_root()
    if git_root:
        git_root = git_root.resolve()

    env_files = []
    current = start_dir
    depth = 0

    while depth < max_depth:
        env_file = current / ".env"
        if env_file.is_file():
            env_files.append(env_file)

        # Stop at git root (inclusive - check git root's .env first)
        if git_root and current == git_root:
            break

        # Stop at filesystem root
        parent = current.parent
        if parent == current:
            break

        current = parent
        depth += 1

    return env_files


def load_environment(
    env_file: Path | None = None,
    no_env: bool = False,
    verbose: bool = False,
) -> list[Path]:
    """Load environment variables from .env files.

    Precedence:
    1. no_env=True → No files loaded
    2. env_file specified → Only that file loaded
    3. Default → cwd .env + parent .env files (merged, cwd wins conflicts)

    Args:
        env_file: Explicit path to load (disables auto-discovery)
        no_env: If True, skip all loading
        verbose: If True, log loaded files (reserved for future use)

    Returns:
        List of loaded .env file paths (in load order)

    Raises:
        FileNotFoundError: If env_file is specified but doesn't exist
    """
    if no_env:
        return []

    if env_file is not None:
        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        load_dotenv(env_file, override=True)
        return [env_file]

    # Default: auto-discovery with merge behavior
    env_files = find_env_files()

    if not env_files:
        return []

    # Load in reverse order: farthest parent first (provides defaults)
    # Then closer files override with override=True
    loaded = []
    for ef in reversed(env_files):
        # All files loaded with override=True so later files (closer to cwd) win
        load_dotenv(ef, override=True)
        loaded.append(ef)

    # Return in cwd-to-parent order (same as find_env_files)
    return list(reversed(loaded))
