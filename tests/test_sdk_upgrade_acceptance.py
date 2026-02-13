"""Acceptance tests for Copilot SDK upgrade (0.1.16 → 0.1.23).

Validates each acceptance scenario from the SDK upgrade objective.
Tests exercise REAL implementation code — no mocking of core functionality.
"""

import importlib.metadata
import subprocess
import sys

import pytest


class TestSDKUpgradeAcceptance:
    """Acceptance scenarios for the SDK version bump."""

    # ------------------------------------------------------------------
    # AT-001: Dependency Update and Resolution
    # ------------------------------------------------------------------
    def test_at_001_uv_lock_contains_new_version(self):
        """uv.lock reflects github-copilot-sdk 0.1.23."""
        from pathlib import Path

        lock_path = Path(__file__).resolve().parents[1] / "uv.lock"
        lock_text = lock_path.read_text(encoding="utf-8")
        assert 'name = "github-copilot-sdk"' in lock_text
        assert "0.1.23" in lock_text
        # Ensure old version is NOT present
        assert "0.1.16" not in lock_text

    def test_at_001_pyproject_pins_new_version(self):
        """pyproject.toml pins github-copilot-sdk==0.1.23."""
        from pathlib import Path

        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        pyproject_text = pyproject_path.read_text(encoding="utf-8")
        assert "github-copilot-sdk==0.1.23" in pyproject_text

    def test_at_001_installed_version_is_0_1_23(self):
        """Installed package metadata reports 0.1.23."""
        version = importlib.metadata.version("github-copilot-sdk")
        assert version == "0.1.23"

    # ------------------------------------------------------------------
    # AT-002: Full Test Suite Passes (meta — just verify import chain)
    # ------------------------------------------------------------------
    def test_at_002_sdk_imports_successfully(self):
        """Core SDK imports work with the new version."""
        from copilot import CopilotClient  # noqa: F401
        from copilot.generated.session_events import SessionEventType  # noqa: F401

    def test_at_002_teambot_sdk_client_imports(self):
        """TeamBot SDK client module loads without errors."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError  # noqa: F401

    # ------------------------------------------------------------------
    # AT-003: Linting Passes
    # ------------------------------------------------------------------
    @pytest.mark.acceptance
    @pytest.mark.slow
    def test_at_003_ruff_check_passes(self):
        """ruff check exits with code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
            timeout=30,
        )
        assert result.returncode == 0, f"ruff check failed:\n{result.stdout}\n{result.stderr}"

    @pytest.mark.acceptance
    @pytest.mark.slow
    def test_at_003_ruff_format_check_passes(self):
        """ruff format --check exits with code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--check", "."],
            capture_output=True,
            text=True,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
            timeout=30,
        )
        assert result.returncode == 0, f"ruff format failed:\n{result.stdout}\n{result.stderr}"

    # ------------------------------------------------------------------
    # AT-004: CLI Startup
    # ------------------------------------------------------------------
    def test_at_004_cli_help_runs(self):
        """'teambot --help' exits 0 and prints help text."""
        result = subprocess.run(
            [sys.executable, "-m", "teambot.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
            timeout=10,
        )
        assert result.returncode == 0, f"teambot --help failed:\n{result.stderr}"
        assert "TeamBot" in result.stdout

    # ------------------------------------------------------------------
    # AT-005: /help Displays SDK Version
    # ------------------------------------------------------------------
    def test_at_005_help_contains_sdk_version_label(self):
        """General /help output contains 'Copilot SDK:' label."""
        from teambot.repl.commands import handle_help

        result = handle_help([])
        assert result.success is True
        assert "Copilot SDK:" in result.output

    def test_at_005_help_contains_actual_version(self):
        """General /help output contains the actual installed version string."""
        from teambot.repl.commands import handle_help

        result = handle_help([])
        installed = importlib.metadata.version("github-copilot-sdk")
        assert installed in result.output, (
            f"Expected version '{installed}' in help output, got:\n{result.output[:120]}"
        )

    # ------------------------------------------------------------------
    # AT-006: /help agent and /help parallel Unaffected
    # ------------------------------------------------------------------
    def test_at_006_help_agent_no_sdk_version(self):
        """/help agent does NOT contain 'Copilot SDK:' (topic-specific)."""
        from teambot.repl.commands import handle_help

        result = handle_help(["agent"])
        assert result.success is True
        assert "Copilot SDK:" not in result.output
        # Still contains expected content
        assert "@pm" in result.output
        assert "builder" in result.output.lower()

    def test_at_006_help_parallel_no_sdk_version(self):
        """/help parallel does NOT contain 'Copilot SDK:' (topic-specific)."""
        from teambot.repl.commands import handle_help

        result = handle_help(["parallel"])
        assert result.success is True
        assert "Copilot SDK:" not in result.output
        # Still contains expected content
        assert "Background" in result.output or "background" in result.output
        assert "/tasks" in result.output

    # ------------------------------------------------------------------
    # AT-007: SDK Client Lifecycle
    # ------------------------------------------------------------------
    def test_at_007_sdk_client_init(self):
        """CopilotSDKClient instantiates without error."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        client = CopilotSDKClient()
        assert client.is_available()  # SDK is installed
        assert client._started is False
        assert client._authenticated is False

    def test_at_007_check_auth_handles_both_dict_and_dataclass(self):
        """_check_auth handles both dict (test mocks) and dataclass (real SDK) responses."""
        import inspect

        from teambot.copilot.sdk_client import CopilotSDKClient

        source = inspect.getsource(CopilotSDKClient._check_auth)
        # Must handle dict responses with .get()
        assert '.get("isAuthenticated"' in source or ".get('isAuthenticated'" in source
        # Must also handle dataclass responses with getattr()
        assert "getattr(" in source
        # Must check isinstance to distinguish between them
        assert "isinstance(" in source

    def test_at_007_list_sessions_empty_without_client(self):
        """list_sessions returns [] when client not started."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        client = CopilotSDKClient()
        assert client.list_sessions() == []

    # ------------------------------------------------------------------
    # AT-008: Streaming Mode
    # ------------------------------------------------------------------
    def test_at_008_event_type_enum_available(self):
        """SessionEventType enum has expected streaming values."""
        from copilot.generated.session_events import SessionEventType

        # These are the event types TeamBot checks in _execute_streaming_once
        assert hasattr(SessionEventType, "ASSISTANT_MESSAGE_DELTA")
        assert hasattr(SessionEventType, "SESSION_IDLE")
        assert hasattr(SessionEventType, "SESSION_ERROR")
        assert hasattr(SessionEventType, "ABORT")

    def test_at_008_streaming_method_signature(self):
        """execute_streaming method exists with expected signature."""
        import inspect

        from teambot.copilot.sdk_client import CopilotSDKClient

        sig = inspect.signature(CopilotSDKClient.execute_streaming)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "agent_id" in params
        assert "prompt" in params
        assert "on_chunk" in params
