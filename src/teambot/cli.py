"""TeamBot CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from teambot import __version__
from teambot.config.loader import ConfigError, ConfigLoader, create_default_config
from teambot.visualization.console import ConsoleDisplay

if TYPE_CHECKING:
    from teambot.orchestration import ExecutionLoop, ExecutionResult


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for TeamBot."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="teambot",
        description="TeamBot - Autonomous AI agent teams for software development",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize TeamBot configuration")
    init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing configuration"
    )

    # run command
    run_parser = subparsers.add_parser("run", help="Run TeamBot with an objective")
    run_parser.add_argument("objective", nargs="?", help="Path to objective markdown file")
    run_parser.add_argument(
        "-c", "--config", default="teambot.json", help="Configuration file path"
    )
    run_parser.add_argument(
        "--resume", action="store_true", help="Resume interrupted orchestration"
    )
    run_parser.add_argument(
        "--max-hours", type=float, default=8.0, help="Maximum execution hours (default: 8)"
    )

    # status command
    subparsers.add_parser("status", help="Show TeamBot status")

    return parser


def cmd_init(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Initialize TeamBot configuration."""
    config_path = Path("teambot.json")

    if config_path.exists() and not args.force:
        display.print_error(f"Configuration already exists: {config_path}")
        display.print_warning("Use --force to overwrite")
        return 1

    # Create default config
    config = create_default_config()
    loader = ConfigLoader()
    loader.save(config, config_path)

    # Create .teambot directory
    teambot_dir = Path(".teambot")
    teambot_dir.mkdir(exist_ok=True)
    (teambot_dir / "history").mkdir(exist_ok=True)
    (teambot_dir / "state").mkdir(exist_ok=True)

    display.print_success(f"Created configuration: {config_path}")
    display.print_success(f"Created directory: {teambot_dir}")

    # Show agents
    display.print_header("Configured Agents")
    for agent in config["agents"]:
        display.add_agent(agent["id"], agent["persona"], agent.get("display_name"))
    display.print_status()

    return 0


def cmd_run(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Run TeamBot with an objective."""
    config_path = Path(args.config)
    teambot_dir = Path(".teambot")

    if not config_path.exists():
        display.print_error(f"Configuration not found: {config_path}")
        display.print_warning("Run 'teambot init' first")
        return 1

    try:
        loader = ConfigLoader()
        config = loader.load(config_path)
    except ConfigError as e:
        display.print_error(f"Configuration error: {e}")
        return 1

    # Resume mode
    if getattr(args, "resume", False):
        return _run_orchestration_resume(config, teambot_dir, display)

    # Load objective if provided
    objective = None
    objective_path = None
    if args.objective:
        objective_path = Path(args.objective)
        if not objective_path.exists():
            display.print_error(f"Objective file not found: {objective_path}")
            return 1
        objective = objective_path.read_text()

    display.print_header("TeamBot Starting")

    # Setup agents display
    for agent_config in config["agents"]:
        display.add_agent(
            agent_config["id"],
            agent_config["persona"],
            agent_config.get("display_name"),
        )

    display.print_status()

    if objective and objective_path:
        return _run_orchestration(
            objective_path, config, teambot_dir, getattr(args, "max_hours", 8.0), display
        )

    # No objective - run interactive mode
    display.print_success("Starting interactive mode")

    from teambot.repl import run_interactive_mode

    try:
        asyncio.run(run_interactive_mode(console=display.console))
    except KeyboardInterrupt:
        display.print_warning("Interrupted")

    return 0


async def _run_orchestration_async(
    loop: ExecutionLoop,
    display: ConsoleDisplay,
    on_progress: Callable[[str, dict], None],
) -> ExecutionResult:
    """Async implementation of orchestration run."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    sdk_client = CopilotSDKClient()
    if not sdk_client.is_available():
        display.print_error("Copilot SDK not available - install github-copilot-sdk")
        raise RuntimeError("SDK not available")

    try:
        await sdk_client.start()
        return await loop.run(sdk_client=sdk_client, on_progress=on_progress)
    finally:
        await sdk_client.stop()


def _run_orchestration(
    objective_path: Path,
    config: dict,
    teambot_dir: Path,
    max_hours: float,
    display: ConsoleDisplay,
) -> int:
    """Run file-based orchestration."""
    import signal

    from teambot.orchestration import ExecutionLoop, ExecutionResult

    # Ensure teambot dir exists
    teambot_dir.mkdir(exist_ok=True)

    display.print_success(f"Running objective: {objective_path}")
    display.print_success(f"Max execution time: {max_hours} hours")

    try:
        loop = ExecutionLoop(
            objective_path=objective_path,
            config=config,
            teambot_dir=teambot_dir,
            max_hours=max_hours,
        )
    except FileNotFoundError as e:
        display.print_error(str(e))
        return 1

    # Setup signal handler for cancellation
    def handle_interrupt(sig: int, frame: object) -> None:
        display.print_warning("Cancellation requested, saving state...")
        loop.cancel()

    signal.signal(signal.SIGINT, handle_interrupt)

    def on_progress(event_type: str, data: dict) -> None:
        if event_type == "stage_changed":
            display.print_success(f"Stage: {data.get('stage', 'unknown')}")
        elif event_type == "agent_running":
            display.print_success(f"Agent {data.get('agent_id')} running")
        elif event_type == "agent_complete":
            display.print_success(f"Agent {data.get('agent_id')} complete")
        elif event_type == "review_progress":
            display.print_success(data.get("message", ""))

    try:
        result = asyncio.run(_run_orchestration_async(loop, display, on_progress))

        if result == ExecutionResult.COMPLETE:
            display.print_success("Objective completed!")
            return 0
        elif result == ExecutionResult.CANCELLED:
            display.print_warning("Cancelled. Resume with: teambot run --resume")
            return 130
        elif result == ExecutionResult.TIMEOUT:
            display.print_warning("Time limit reached. Resume with: teambot run --resume")
            return 1
        elif result == ExecutionResult.REVIEW_FAILED:
            display.print_error("Review failed after 4 iterations. See .teambot/failures/")
            return 1
        else:
            display.print_error(f"Execution ended with: {result.value}")
            return 1

    except Exception as e:
        display.print_error(f"Execution error: {e}")
        return 1


async def _run_orchestration_resume_async(
    loop: ExecutionLoop,
    display: ConsoleDisplay,
    on_progress: Callable[[str, dict], None],
) -> ExecutionResult:
    """Async implementation of orchestration resume."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    sdk_client = CopilotSDKClient()
    if not sdk_client.is_available():
        display.print_error("Copilot SDK not available - install github-copilot-sdk")
        raise RuntimeError("SDK not available")

    try:
        await sdk_client.start()
        return await loop.run(sdk_client=sdk_client, on_progress=on_progress)
    finally:
        await sdk_client.stop()


def _run_orchestration_resume(config: dict, teambot_dir: Path, display: ConsoleDisplay) -> int:
    """Resume interrupted orchestration."""
    import signal

    from teambot.orchestration import ExecutionLoop, ExecutionResult

    display.print_header("TeamBot Resuming")

    try:
        loop = ExecutionLoop.resume(teambot_dir, config)
    except ValueError as e:
        display.print_error(str(e))
        display.print_warning("No interrupted session to resume")
        return 1

    display.print_success(f"Resuming from stage: {loop.current_stage.name}")
    display.print_success(f"Prior elapsed: {loop.time_manager.format_elapsed()}")

    # Setup signal handler for cancellation
    def handle_interrupt(sig: int, frame: object) -> None:
        display.print_warning("Cancellation requested, saving state...")
        loop.cancel()

    signal.signal(signal.SIGINT, handle_interrupt)

    def on_progress(event_type: str, data: dict) -> None:
        if event_type == "stage_changed":
            display.print_success(f"Stage: {data.get('stage', 'unknown')}")

    try:
        result = asyncio.run(_run_orchestration_resume_async(loop, display, on_progress))

        if result == ExecutionResult.COMPLETE:
            display.print_success("Objective completed!")
            return 0
        elif result == ExecutionResult.CANCELLED:
            display.print_warning("Cancelled. Resume with: teambot run --resume")
            return 130
        elif result == ExecutionResult.TIMEOUT:
            display.print_warning("Time limit reached. Resume with: teambot run --resume")
            return 1
        elif result == ExecutionResult.REVIEW_FAILED:
            display.print_error("Review failed after 4 iterations. See .teambot/failures/")
            return 1
        else:
            return 1

    except Exception as e:
        display.print_error(f"Execution error: {e}")
        return 1


def cmd_status(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Show TeamBot status."""
    teambot_dir = Path(".teambot")

    if not teambot_dir.exists():
        display.print_error("TeamBot not initialized in this directory")
        display.print_warning("Run 'teambot init' first")
        return 1

    display.print_header("TeamBot Status")

    # Count history files
    history_dir = teambot_dir / "history"
    if history_dir.exists():
        history_count = len(list(history_dir.glob("*.md")))
        display.print_success(f"History files: {history_count}")
    else:
        display.print_warning("No history directory found")

    # Check config
    config_path = Path("teambot.json")
    if config_path.exists():
        display.print_success(f"Configuration: {config_path}")
    else:
        display.print_warning("No configuration file found")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(getattr(args, "verbose", False))

    display = ConsoleDisplay()

    if args.command == "init":
        return cmd_init(args, display)
    elif args.command == "run":
        return cmd_run(args, display)
    elif args.command == "status":
        return cmd_status(args, display)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
