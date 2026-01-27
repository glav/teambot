"""Cross-platform window spawning for agent processes."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


class WindowSpawnError(Exception):
    """Raised when window spawning fails."""

    pass


class WindowManager:
    """Manages spawning of agent windows across platforms."""

    # Linux terminal emulators in order of preference
    LINUX_TERMINALS = [
        ("gnome-terminal", "--"),
        ("konsole", "-e"),
        ("xfce4-terminal", "-e"),
        ("xterm", "-e"),
        ("terminator", "-e"),
    ]

    def __init__(self):
        self.system = platform.system()
        self._linux_terminal: tuple[str, str] | None = None
        self._processes: dict[str, subprocess.Popen[Any]] = {}

    def _detect_linux_terminal(self) -> tuple[str, str] | None:
        """Detect available terminal emulator on Linux."""
        if self._linux_terminal:
            return self._linux_terminal

        for name, flag in self.LINUX_TERMINALS:
            if shutil.which(name):
                self._linux_terminal = (name, flag)
                return self._linux_terminal
        return None

    def spawn_window(
        self,
        agent_id: str,
        script: str | Path,
        args: list[str] | None = None,
        title: str | None = None,
        working_dir: str | Path | None = None,
    ) -> subprocess.Popen[Any]:
        """Spawn a new terminal window running the given script."""
        args = args or []
        python = sys.executable
        full_args = [python, str(script)] + args

        cwd = str(working_dir) if working_dir else None

        if self.system == "Windows":
            process = self._spawn_windows(full_args, title, cwd)
        elif self.system == "Darwin":
            process = self._spawn_macos(full_args, title, cwd)
        else:  # Linux/Unix
            process = self._spawn_linux(full_args, title, cwd)

        self._processes[agent_id] = process
        return process

    def _spawn_windows(
        self, args: list[str], title: str | None, cwd: str | None
    ) -> subprocess.Popen[Any]:
        """Spawn on Windows using CREATE_NEW_CONSOLE."""
        # Title can be set via start command
        if title:
            cmd = ["cmd", "/c", "start", title] + args
        else:
            cmd = args

        # CREATE_NEW_CONSOLE is Windows-only
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        return subprocess.Popen(cmd, creationflags=creationflags, cwd=cwd)

    def _spawn_macos(
        self, args: list[str], title: str | None, cwd: str | None
    ) -> subprocess.Popen[Any]:
        """Spawn on macOS using AppleScript and Terminal.app."""
        cmd_str = " ".join(f'"{arg}"' for arg in args)
        if cwd:
            cmd_str = f"cd {cwd} && {cmd_str}"

        applescript = f'''
        tell application "Terminal"
            activate
            do script "{cmd_str}"
        end tell
        '''
        return subprocess.Popen(["osascript", "-e", applescript])

    def _spawn_linux(
        self, args: list[str], title: str | None, cwd: str | None
    ) -> subprocess.Popen[Any]:
        """Spawn on Linux using detected terminal emulator."""
        terminal = self._detect_linux_terminal()
        if not terminal:
            raise WindowSpawnError(
                "No supported terminal emulator found. "
                f"Please install one of: {[t[0] for t in self.LINUX_TERMINALS]}"
            )

        name, flag = terminal

        # Build command based on terminal
        if name == "gnome-terminal":
            cmd = ["gnome-terminal"]
            if cwd:
                cmd.extend(["--working-directory", cwd])
            if title:
                cmd.extend(["--title", title])
            cmd.extend(["--", *args])
        elif name == "konsole":
            cmd = ["konsole"]
            if cwd:
                cmd.extend(["--workdir", cwd])
            cmd.extend(["-e", *args])
        elif name == "xfce4-terminal":
            cmd = ["xfce4-terminal"]
            if cwd:
                cmd.extend(["--working-directory", cwd])
            if title:
                cmd.extend(["--title", title])
            cmd.extend(["-e", " ".join(args)])
        else:
            # Generic fallback (xterm, terminator)
            cmd = [name, flag, " ".join(args)]

        return subprocess.Popen(cmd, start_new_session=True, cwd=cwd)

    def get_process(self, agent_id: str) -> subprocess.Popen[Any] | None:
        """Get the process for an agent."""
        return self._processes.get(agent_id)

    def is_running(self, agent_id: str) -> bool:
        """Check if an agent's window process is still running."""
        process = self._processes.get(agent_id)
        if process is None:
            return False
        return process.poll() is None

    def terminate(self, agent_id: str) -> None:
        """Terminate an agent's window process."""
        process = self._processes.get(agent_id)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if agent_id in self._processes:
            del self._processes[agent_id]

    def terminate_all(self) -> None:
        """Terminate all spawned window processes."""
        for agent_id in list(self._processes.keys()):
            self.terminate(agent_id)

    def get_active_agents(self) -> list[str]:
        """Get list of agents with active windows."""
        return [aid for aid in self._processes if self.is_running(aid)]
