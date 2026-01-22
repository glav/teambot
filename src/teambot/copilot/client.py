"""Copilot CLI client for executing prompts."""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CopilotResult:
    """Result from a Copilot CLI execution."""

    success: bool
    output: str
    error: str | None = None
    exit_code: int = 0
    prompt: str = ""


@dataclass
class CopilotConfig:
    """Configuration for Copilot CLI invocation."""

    allow_all_tools: bool = True
    allow_all_paths: bool = False
    additional_dirs: list[str] = field(default_factory=list)
    model: str | None = None
    timeout: int = 300  # 5 minutes default


class CopilotClient:
    """Client for invoking the Copilot CLI."""

    def __init__(
        self,
        working_dir: Path | None = None,
        config: CopilotConfig | None = None,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.config = config or CopilotConfig()
        self._copilot_path: str | None = None

    @property
    def copilot_path(self) -> str:
        """Get the path to the copilot CLI."""
        if self._copilot_path is None:
            self._copilot_path = shutil.which("copilot")
            if self._copilot_path is None:
                raise RuntimeError(
                    "Copilot CLI not found. Please install it from "
                    "https://github.com/github/copilot-cli"
                )
        return self._copilot_path

    def is_available(self) -> bool:
        """Check if Copilot CLI is available."""
        try:
            return self.copilot_path is not None
        except RuntimeError:
            return False

    def execute(self, prompt: str, context: str | None = None) -> CopilotResult:
        """Execute a prompt using the Copilot CLI in non-interactive mode.

        Args:
            prompt: The prompt/task to send to Copilot CLI
            context: Optional additional context to prepend to the prompt

        Returns:
            CopilotResult with output and status
        """
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n{prompt}"

        cmd = self._build_command(full_prompt)
        logger.info(f"Executing Copilot CLI: {' '.join(cmd[:3])}...")
        logger.debug(f"Full command: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )

            success = result.returncode == 0
            return CopilotResult(
                success=success,
                output=result.stdout,
                error=result.stderr if result.stderr else None,
                exit_code=result.returncode,
                prompt=full_prompt,
            )

        except subprocess.TimeoutExpired as e:
            logger.error(f"Copilot CLI timed out after {self.config.timeout}s")
            return CopilotResult(
                success=False,
                output=e.stdout.decode() if e.stdout else "",
                error=f"Timeout after {self.config.timeout} seconds",
                exit_code=-1,
                prompt=full_prompt,
            )
        except FileNotFoundError:
            logger.error("Copilot CLI not found")
            return CopilotResult(
                success=False,
                output="",
                error="Copilot CLI not found in PATH",
                exit_code=-1,
                prompt=full_prompt,
            )
        except Exception as e:
            logger.error(f"Copilot CLI error: {e}")
            return CopilotResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                prompt=full_prompt,
            )

    def _build_command(self, prompt: str) -> list[str]:
        """Build the Copilot CLI command with arguments."""
        cmd = [self.copilot_path, "-p", prompt]

        if self.config.allow_all_tools:
            cmd.append("--allow-all-tools")

        if self.config.allow_all_paths:
            cmd.append("--allow-all-paths")

        for dir_path in self.config.additional_dirs:
            cmd.extend(["--add-dir", dir_path])

        if self.config.model:
            cmd.extend(["--model", self.config.model])

        return cmd

    def execute_with_session(self, prompt: str, session_id: str | None = None) -> CopilotResult:
        """Execute with session continuation (for multi-turn interactions).

        Note: Session continuation requires the --continue flag and is
        primarily useful for interactive mode. For non-interactive tasks,
        use execute() directly.
        """
        # For now, delegate to regular execute
        # Session management could be added later if needed
        return self.execute(prompt)
