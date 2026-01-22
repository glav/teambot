"""TeamBot CLI entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from teambot import __version__
from teambot.config.loader import ConfigError, ConfigLoader, create_default_config
from teambot.orchestrator import Orchestrator
from teambot.visualization.console import ConsoleDisplay


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

    # Load objective if provided
    objective = None
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

    # Create orchestrator (unused for now - full orchestration not implemented)
    _ = Orchestrator(config)

    display.print_status()

    if objective:
        display.print_success("Objective loaded")
    else:
        display.print_warning("No objective file provided - running in interactive mode")

    display.print_success("TeamBot initialized successfully")
    display.print_warning("Full agent orchestration not yet implemented")

    return 0


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
