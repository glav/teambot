"""TeamBot CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from teambot import __version__
from teambot.config.loader import ConfigError, ConfigLoader, create_default_config
from teambot.notifications.config import create_event_bus_from_config
from teambot.visualization.animation import play_startup_animation
from teambot.visualization.console import ConsoleDisplay

if TYPE_CHECKING:
    from teambot.notifications.event_bus import EventBus
    from teambot.orchestration import ExecutionLoop, ExecutionResult


COPILOT_CLI_INSTALL_URL = "https://githubnext.com/projects/copilot-cli/"

# Constants for AGENTS.md template reference update
OBJECTIVE_TEMPLATE_MARKER = "## Objective Template"

OBJECTIVE_TEMPLATE_SECTION = """
## Objective Template

TeamBot provides an objective template for defining development tasks:

**File**: `docs/sdd-objective-template.md`

Copy this template, fill in the sections, then run:

```bash
teambot run objectives/my-feature.md
```
"""


def _agents_md_has_template_reference(agents_md_path: Path) -> bool:
    """Check if AGENTS.md already has the objective template reference.

    Args:
        agents_md_path: Path to AGENTS.md file

    Returns:
        True if the template reference section exists, False otherwise
    """
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        return OBJECTIVE_TEMPLATE_MARKER in content
    except OSError:
        return False


def _should_update_agents_md(results: list) -> bool:
    """Determine if AGENTS.md should be updated with template reference.

    Update is triggered when:
    1. sdd-objective-template.md was successfully copied (newly added)
    2. AGENTS.md exists but was skipped (not overwritten)

    Args:
        results: List of CopyResult from scaffold copying

    Returns:
        True if AGENTS.md should be updated
    """
    template_copied = False
    agents_md_skipped = False

    for result in results:
        if result.source == "sdd-objective-template.md" and result.copied:
            template_copied = True
        if result.source == "AGENTS.md" and result.reason == "skipped_exists":
            agents_md_skipped = True

    return template_copied and agents_md_skipped


def _update_agents_md_with_template_reference(
    results: list,
    target_root: Path,
    display,
) -> bool:
    """Update AGENTS.md with objective template reference if needed.

    Only updates if:
    1. AGENTS.md exists but was skipped (not force-overwritten)
    2. sdd-objective-template.md was successfully copied
    3. AGENTS.md doesn't already have the template reference

    Args:
        results: Copy results from scaffold operation
        target_root: Root directory (typically Path.cwd())
        display: Console display for user feedback (can be None)

    Returns:
        True if AGENTS.md was updated, False if skipped
    """
    if not _should_update_agents_md(results):
        return False

    agents_md_path = target_root / "AGENTS.md"

    if not agents_md_path.exists():
        return False

    if _agents_md_has_template_reference(agents_md_path):
        if display:
            display.print_info("  AGENTS.md already has objective template reference")
        return False

    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # Ensure proper newline separation
        if content and not content.endswith("\n"):
            content += "\n"
        content += OBJECTIVE_TEMPLATE_SECTION.strip() + "\n"
        agents_md_path.write_text(content, encoding="utf-8")

        if display:
            display.print_success("  Updated AGENTS.md with objective template reference")
        return True
    except OSError as e:
        logging.debug(f"Failed to update AGENTS.md: {e}")
        return False


async def _refresh_model_cache_async() -> bool:
    """Async helper to refresh model cache from SDK.

    Returns:
        True if refresh succeeded, False otherwise.
    """
    from teambot.config.schema import refresh_models

    return await refresh_models()


def _refresh_model_cache(display: ConsoleDisplay) -> bool:
    """Refresh model cache, displaying status.

    Args:
        display: Console display for output.

    Returns:
        True if refresh succeeded, False otherwise.
    """
    try:
        success = asyncio.run(_refresh_model_cache_async())
        if success:
            display.print_success("Model cache refreshed")
            return True
        else:
            display.print_warning("Could not refresh model cache - models may not be available")
            display.print_warning("Run '/models --refresh' later to update model list")
            return False
    except Exception as e:
        logging.debug(f"Model cache refresh failed: {e}")
        display.print_warning("Model cache refresh failed")
        display.print_warning("Run '/models --refresh' later to update model list")
        return False


async def _check_auth_async() -> tuple[bool, str | None]:
    """Check Copilot authentication status.

    Returns:
        Tuple of (is_authenticated, error_message).
    """
    from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

    client = CopilotSDKClient()
    if not client.is_available():
        return False, "Copilot SDK not available"

    try:
        await client.start()
        is_auth = client.is_authenticated()
        await client.stop()
        return is_auth, None
    except SDKClientError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def _check_copilot_authentication(display: ConsoleDisplay) -> bool:
    """Check and display Copilot authentication status.

    Args:
        display: Console display for output.

    Returns:
        True if authenticated, False otherwise.
    """
    try:
        is_auth, error = asyncio.run(_check_auth_async())

        if is_auth:
            display.print_success("Copilot authenticated")
            return True
        else:
            display.print_warning("Copilot not authenticated")
            if error and "not available" not in error.lower():
                display.print_warning(f"  {error}")
            display.print_info("  Run 'copilot login' to authenticate")
            display.print_info("  Or set GITHUB_TOKEN environment variable")
            return False
    except Exception as e:
        logging.debug(f"Could not check authentication: {e}")
        display.print_warning("Could not verify authentication status")
        display.print_info("Run 'copilot login' to ensure you're authenticated")
        return False


def _check_copilot_authentication_blocking(display: ConsoleDisplay) -> bool:
    """Check Copilot authentication status (blocking version for cmd_run).

    Unlike _check_copilot_authentication which continues with warnings,
    this version treats authentication failure as a blocking error.

    Args:
        display: Console display for output.

    Returns:
        True if authenticated, False otherwise (blocks execution).
    """
    try:
        is_auth, error = asyncio.run(_check_auth_async())

        if is_auth:
            return True
        else:
            display.print_error("Copilot not authenticated")
            if error and "not available" not in error.lower():
                display.print_error(f"  {error}")
            display.print_info("Run 'copilot login' to authenticate")
            return False
    except Exception as e:
        logging.debug(f"Could not check authentication: {e}")
        display.print_error("Could not verify authentication status")
        display.print_info("Run 'copilot login' to ensure you're authenticated")
        return False


def _ensure_model_cache(display: ConsoleDisplay) -> None:
    """Ensure model cache is available, refreshing if needed.

    Checks if model cache exists. If missing or empty, automatically refreshes
    from SDK with status feedback.

    Expired cache handling is intentionally left to the existing warning
    path in schema._ensure_models_loaded() - this function only handles
    the first-run case when no cache exists at all or cache is empty.

    This is non-blocking - if refresh fails, execution continues
    and ConfigLoader will report specific validation errors.

    Args:
        display: Console display for output.
    """
    from teambot.config.model_cache import load_cache

    cache = load_cache()

    # Only refresh when cache is missing or empty
    # Expired cache is intentionally used as-is (schema will warn)
    if cache is None:
        display.print_info("Refreshing model cache...")
        _refresh_model_cache(display)
    elif not cache.models:
        display.print_info("Model cache is empty, refreshing...")
        _refresh_model_cache(display)
    # Expired cache: don't refresh, let schema handle with warning


def _display_post_init_guidance(display: ConsoleDisplay) -> None:
    """Display post-init recommended next steps.

    Loads guidance from package file for maintainability.
    Falls back to basic guidance if file cannot be loaded.
    """
    try:
        from importlib.resources import files

        pkg = files("teambot")
        guidance_path = pkg.joinpath("scaffolds", "init-next-steps.md")

        # Handle both traversable and path-like objects
        if hasattr(guidance_path, "read_text"):
            content = guidance_path.read_text(encoding="utf-8")
        else:
            content = Path(str(guidance_path)).read_text(encoding="utf-8")

        display.print_info("")
        display.print_info("=== Recommended Next Steps ===")

        # Parse and display content (skip markdown headers/fences)
        for line in content.strip().split("\n"):
            line_stripped = line.strip()
            if line_stripped.startswith("## ") or line_stripped.startswith("# "):
                continue  # Skip markdown headers
            elif line_stripped.startswith("```"):
                continue  # Skip code fence markers
            elif line_stripped:
                display.print_info(f"  {line}")

    except Exception as e:
        logging.debug(f"Failed to load init guidance file: {e}")
        # Fallback to basic hardcoded guidance
        display.print_info("")
        display.print_info("=== Recommended Next Steps ===")
        display.print_info("  1. Edit teambot.json to customize per-agent models")
        display.print_info("  2. Create an objective file in docs/objectives/")
        display.print_info("  3. Run 'teambot run objectives/your-task.md'")
        display.print_info("  4. Or use 'teambot run' for interactive mode")


def check_copilot_cli(display: ConsoleDisplay | None = None) -> bool:
    """Check if Copilot CLI is installed and accessible.

    Args:
        display: Optional console display for output.

    Returns:
        True if Copilot CLI is available, False otherwise.
    """
    if shutil.which("copilot") is not None:
        return True

    # Print helpful error message
    if display is None:
        display = ConsoleDisplay()

    display.print_error("GitHub Copilot CLI is required but not found.")
    display.print_warning(f"Install from: {COPILOT_CLI_INSTALL_URL}")
    display.print_warning("After installing, authenticate with: copilot login")

    return False


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
    parser.add_argument("--no-animation", action="store_true", help="Disable startup animation")

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
    run_parser.add_argument(
        "--log-to-console",
        action="store_true",
        help="Enable console logging output (useful for debugging interactive mode)",
    )

    # status command
    subparsers.add_parser("status", help="Show TeamBot status")

    return parser


def _should_setup_notifications(display: ConsoleDisplay) -> bool:
    """Ask user if they want to configure notifications."""
    import sys

    # Skip in non-interactive mode (e.g., testing)
    if not sys.stdin.isatty():
        return False

    display.print_info("")
    display.print_info("=== Optional: Real-Time Notifications ===")
    display.print_info("TeamBot can send notifications via Telegram when stages complete.")
    try:
        response = input("Enable real-time notifications? [y/N]: ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _setup_telegram_notifications(config: dict, display: ConsoleDisplay) -> bool:
    """Guide user through Telegram notification setup."""
    display.print_info("")
    display.print_info("=== Telegram Bot Setup ===")
    display.print_info("1. Open Telegram and search for @BotFather")
    display.print_info("2. Send /newbot and follow the prompts")
    display.print_info("3. Copy the bot token you receive")
    display.print_info("")

    try:
        proceed = input("Ready to enter credentials? [Y/n]: ").strip().lower()
        if proceed in ("n", "no"):
            display.print_warning("Skipping notification setup")
            return False

        # Get bot token env var name (with default)
        token_env = input("Environment variable for bot token [TEAMBOT_TELEGRAM_TOKEN]: ").strip()
        if not token_env:
            token_env = "TEAMBOT_TELEGRAM_TOKEN"

        # Get chat ID env var name (with default)
        display.print_info("")
        display.print_info("To get your chat ID:")
        display.print_info("1. Send any message to your new bot")
        display.print_info("2. Visit: https://api.telegram.org/bot<TOKEN>/getUpdates")
        display.print_info("3. Look for 'chat':{'id': <YOUR_CHAT_ID>}")
        display.print_info("")
        chat_id_env = input("Environment variable for chat ID [TEAMBOT_TELEGRAM_CHAT_ID]: ").strip()
        if not chat_id_env:
            chat_id_env = "TEAMBOT_TELEGRAM_CHAT_ID"

        # Get notification mode
        display.print_info("")
        display.print_info("=== Notification Frequency ===")
        display.print_info("Choose how many notifications to receive:")
        display.print_info("  1. stages_only  - Major milestones only (recommended)")
        display.print_info("  2. agent_status - Stage + agent lifecycle events")
        display.print_info("  3. all          - All events (verbose)")
        display.print_info("")

        mode_input = input("Notification mode [1/2/3, default: 1]: ").strip()
        mode_map = {"1": "stages_only", "2": "agent_status", "3": "all", "": "stages_only"}
        notification_mode = mode_map.get(mode_input, "stages_only")

        # Add notifications config
        config["notifications"] = {
            "enabled": True,
            "channels": [
                {
                    "type": "telegram",
                    "token": f"${{{token_env}}}",
                    "chat_id": f"${{{chat_id_env}}}",
                    "notification_mode": notification_mode,
                }
            ],
        }

        display.print_info("")
        display.print_success("Notification configuration added!")
        display.print_info(f"  Mode: {notification_mode}")
        display.print_info("")
        display.print_warning("IMPORTANT: Set these environment variables:")
        display.print_warning(f"  export {token_env}='your-bot-token'")
        display.print_warning(f"  export {chat_id_env}='your-chat-id'")
        display.print_info("")

        return True

    except (EOFError, KeyboardInterrupt):
        display.print_warning("\nSkipping notification setup")
        return False


def cmd_init(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Initialize TeamBot configuration."""
    config_path = Path("teambot.json")
    force = getattr(args, "force", False)

    if config_path.exists() and not force:
        display.print_error(f"Configuration already exists: {config_path}")
        display.print_warning("Use --force to overwrite")
        return 1

    # Create default config
    config = create_default_config()

    # Optional notification setup
    if _should_setup_notifications(display):
        _setup_telegram_notifications(config, display)

    loader = ConfigLoader()
    loader.save(config, config_path)

    # Create .teambot directory
    teambot_dir = Path(".teambot")
    teambot_dir.mkdir(exist_ok=True)
    (teambot_dir / "history").mkdir(exist_ok=True)
    (teambot_dir / "state").mkdir(exist_ok=True)

    display.print_success(f"Created configuration: {config_path}")
    display.print_success(f"Created directory: {teambot_dir}")

    # Copy scaffold files
    from teambot.scaffolds import copy_all_scaffolds

    display.print_success("")
    display.print_success("=== Copying Scaffold Files ===")

    results = copy_all_scaffolds(Path.cwd(), force=force)

    for result in results:
        if result.copied:
            display.print_success(f"  Copied: {result.target}")
        elif result.reason == "skipped_exists":
            display.print_warning(f"  Skipped (exists): {result.target}")
        elif result.reason == "skipped_not_empty":
            display.print_warning(f"  Skipped (not empty): {result.target}")
        elif result.reason == "source_missing":
            display.print_error(f"  Missing from package: {result.source}")

    # Update AGENTS.md with template reference if applicable
    _update_agents_md_with_template_reference(results, Path.cwd(), display)

    display.print_success("")

    # Check authentication and refresh model cache (non-blocking)
    display.print_info("")
    display.print_info("=== Copilot Status ===")
    _check_copilot_authentication(display)
    _refresh_model_cache(display)

    # Show agents
    play_startup_animation(
        console=display.console,
        config=None,
        no_animation_flag=getattr(args, "no_animation", False),
        version=__version__,
    )
    default_model = config.get("default_model")
    for agent in config["agents"]:
        model = agent.get("model") or default_model
        display.add_agent(agent["id"], agent["persona"], agent.get("display_name"), model=model)
    display.print_status()

    # Display recommended next steps
    _display_post_init_guidance(display)

    return 0


def cmd_run(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Run TeamBot with an objective."""
    config_path = Path(args.config)
    teambot_dir = Path(".teambot")

    # Fast-fail if config doesn't exist (no side effects)
    if not config_path.exists():
        display.print_error(f"Configuration not found: {config_path}")
        display.print_warning("Run 'teambot init' first")
        return 1

    # Authentication check (blocking - exit if not authenticated)
    if not _check_copilot_authentication_blocking(display):
        return 1

    # Ensure model cache is available (auto-refresh if needed)
    _ensure_model_cache(display)

    try:
        loader = ConfigLoader()
        config = loader.load(config_path)
    except ConfigError as e:
        display.print_error(f"Configuration error: {e}")
        return 1

    # Configure mode-aware logging after config is loaded
    from teambot.config.logging_config import is_interactive_mode
    from teambot.config.logging_config import setup_logging as setup_mode_logging

    interactive = is_interactive_mode(has_objective=bool(args.objective))
    setup_mode_logging(
        config=config,
        is_interactive=interactive,
        force_console=getattr(args, "log_to_console", False),
        verbose=getattr(args, "verbose", False),
    )

    # Resume mode
    if getattr(args, "resume", False):
        return _run_orchestration_resume(
            config,
            teambot_dir,
            display,
            no_animation=getattr(args, "no_animation", False),
        )

    # Load objective if provided
    objective = None
    objective_path = None
    if args.objective:
        objective_path = Path(args.objective)
        if not objective_path.exists():
            display.print_error(f"Objective file not found: {objective_path}")
            return 1
        objective = objective_path.read_text(encoding="utf-8")

    play_startup_animation(
        console=display.console,
        config=config,
        no_animation_flag=getattr(args, "no_animation", False),
        version=__version__,
    )

    # Setup agents display
    default_model = config.get("default_model")
    for agent_config in config["agents"]:
        model = agent_config.get("model") or default_model
        display.add_agent(
            agent_config["id"],
            agent_config["persona"],
            agent_config.get("display_name"),
            model=model,
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
        asyncio.run(run_interactive_mode(console=display.console, config=config))
    except KeyboardInterrupt:
        display.print_warning("Interrupted")

    return 0


async def _run_orchestration_async(
    loop: ExecutionLoop,
    display: ConsoleDisplay,
    on_progress: Callable[[str, dict], None],
    event_bus: EventBus | None = None,
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
        # Drain pending notifications before shutdown
        if event_bus is not None:
            await event_bus.drain(timeout=5.0)


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

    # Create EventBus for notifications
    feature_name = objective_path.stem
    event_bus = create_event_bus_from_config(config, feature_name=feature_name)

    # Setup signal handler for cancellation
    cancel_count = [0]  # Use list to allow modification in nested function

    def handle_interrupt(sig: int, frame: object) -> None:
        cancel_count[0] += 1
        if cancel_count[0] == 1:
            display.print_warning(
                "Cancellation requested, saving state... (Ctrl+C again to force quit)"
            )
            loop.cancel()
        else:
            # Force exit on second Ctrl+C
            display.print_warning("Force quit")
            raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, handle_interrupt)

    def on_progress(event_type: str, data: dict) -> None:
        # Console display logic
        if event_type == "stage_changed":
            display.print_success(f"Stage: {data.get('stage', 'unknown')}")
        elif event_type == "orchestration_started":
            objective = data.get("objective_name", "orchestration run")
            display.print_success(f"Starting: {objective}")
        elif event_type == "orchestration_completed":
            objective = data.get("objective_name", "orchestration run")
            status = data.get("status", "complete")
            duration = data.get("duration_seconds", 0)
            duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"
            status_str = "[DONE]" if status == "complete" else "[WARN]"
            display.print_success(f"{status_str} Completed: {objective} ({duration_str})")
        elif event_type == "agent_running":
            display.print_success(f"Agent {data.get('agent_id')} running")
        elif event_type == "agent_complete":
            display.print_success(f"Agent {data.get('agent_id')} complete")
        elif event_type == "review_progress":
            display.print_success(data.get("message", ""))
        elif event_type == "acceptance_test_iteration":
            iteration = data.get("iteration", 1)
            max_iter = data.get("max_iterations", 4)
            display.print_success(f"Acceptance test iteration {iteration}/{max_iter}")
        elif event_type == "acceptance_test_fix_start":
            iteration = data.get("iteration", 1)
            failed = data.get("failed_count", 0)
            msg = f"Iteration {iteration}: {failed} tests failed, requesting fix..."
            display.print_warning(msg)
        elif event_type == "acceptance_test_fix_complete":
            iteration = data.get("iteration", 1)
            display.print_success(f"Iteration {iteration}: Fix applied, re-running tests...")
        elif event_type == "acceptance_test_max_iterations_reached":
            iterations = data.get("iterations_used", 4)
            display.print_error(f"Acceptance tests still failing after {iterations} fix attempts")

        # Emit to EventBus for notifications (non-blocking)
        if event_bus is not None:
            event_bus.emit_sync(event_type, data)

    try:
        result = asyncio.run(_run_orchestration_async(loop, display, on_progress, event_bus))

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
    event_bus: EventBus | None = None,
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
        # Drain pending notifications before shutdown
        if event_bus is not None:
            await event_bus.drain(timeout=5.0)


def _run_orchestration_resume(
    config: dict, teambot_dir: Path, display: ConsoleDisplay, no_animation: bool = False
) -> int:
    """Resume interrupted orchestration."""
    import signal

    from teambot.orchestration import ExecutionLoop, ExecutionResult

    play_startup_animation(
        console=display.console,
        config=config,
        no_animation_flag=no_animation,
        version=__version__,
    )

    try:
        loop = ExecutionLoop.resume(teambot_dir, config)
    except ValueError as e:
        display.print_error(str(e))
        display.print_warning("No interrupted session to resume")
        return 1

    display.print_success(f"Resuming from stage: {loop.current_stage.name}")
    display.print_success(f"Prior elapsed: {loop.time_manager.format_elapsed()}")

    # Create EventBus for notifications
    feature_name = getattr(loop, "objective_path", Path("resume")).stem
    event_bus = create_event_bus_from_config(config, feature_name=feature_name)

    # Setup signal handler for cancellation
    cancel_count = [0]  # Use list to allow modification in nested function

    def handle_interrupt(sig: int, frame: object) -> None:
        cancel_count[0] += 1
        if cancel_count[0] == 1:
            display.print_warning(
                "Cancellation requested, saving state... (Ctrl+C again to force quit)"
            )
            loop.cancel()
        else:
            # Force exit on second Ctrl+C
            display.print_warning("Force quit")
            raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, handle_interrupt)

    def on_progress(event_type: str, data: dict) -> None:
        # Console display logic
        if event_type == "stage_changed":
            display.print_success(f"Stage: {data.get('stage', 'unknown')}")
        elif event_type == "orchestration_started":
            objective = data.get("objective_name", "orchestration run")
            display.print_success(f"Starting: {objective}")
        elif event_type == "orchestration_completed":
            objective = data.get("objective_name", "orchestration run")
            status = data.get("status", "complete")
            duration = data.get("duration_seconds", 0)
            duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"
            status_str = "[DONE]" if status == "complete" else "[WARN]"
            display.print_success(f"{status_str} Completed: {objective} ({duration_str})")
        elif event_type == "agent_running":
            display.print_success(f"Agent {data.get('agent_id')} running")
        elif event_type == "agent_complete":
            display.print_success(f"Agent {data.get('agent_id')} complete")
        elif event_type == "review_progress":
            display.print_success(data.get("message", ""))
        elif event_type == "acceptance_test_iteration":
            iteration = data.get("iteration", 1)
            max_iter = data.get("max_iterations", 4)
            display.print_success(f"Acceptance test iteration {iteration}/{max_iter}")
        elif event_type == "acceptance_test_fix_start":
            iteration = data.get("iteration", 1)
            failed = data.get("failed_count", 0)
            msg = f"Iteration {iteration}: {failed} tests failed, requesting fix..."
            display.print_warning(msg)
        elif event_type == "acceptance_test_fix_complete":
            iteration = data.get("iteration", 1)
            display.print_success(f"Iteration {iteration}: Fix applied, re-running tests...")
        elif event_type == "acceptance_test_max_iterations_reached":
            iterations = data.get("iterations_used", 4)
            display.print_error(f"Acceptance tests still failing after {iterations} fix attempts")

        # Emit to EventBus for notifications (non-blocking)
        if event_bus is not None:
            event_bus.emit_sync(event_type, data)

    try:
        result = asyncio.run(_run_orchestration_resume_async(loop, display, on_progress, event_bus))

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
    # Load environment variables from .env file if it exists
    load_dotenv()

    parser = create_parser()
    args = parser.parse_args()

    setup_logging(getattr(args, "verbose", False))

    display = ConsoleDisplay()

    if args.command == "init":
        return cmd_init(args, display)
    elif args.command == "run":
        # Check Copilot CLI availability before running
        if not check_copilot_cli(display):
            return 1
        return cmd_run(args, display)
    elif args.command == "status":
        return cmd_status(args, display)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
