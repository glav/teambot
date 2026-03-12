"""Acceptance test validation for GitHub Copilot SDK upgrade (0.1.23 → 0.1.32).

These tests exercise the REAL implementation code to validate acceptance scenarios.
No mocking of core functionality - tests call actual modules and verify real behavior.
"""

import importlib.metadata
import subprocess
import sys
from pathlib import Path

# Get repository root for file checks
REPO_ROOT = Path(__file__).resolve().parents[1]


class TestSDKUpgradeAcceptanceValidation:
    """Acceptance scenario validation tests for SDK upgrade."""

    # ------------------------------------------------------------------
    # AT-001: SDK Version Updated
    # ------------------------------------------------------------------
    def test_at_001_pyproject_has_new_sdk_version(self):
        """AT-001: pyproject.toml contains github-copilot-sdk==0.1.32."""
        pyproject_path = REPO_ROOT / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        assert "github-copilot-sdk==0.1.32" in content, (
            "pyproject.toml should contain github-copilot-sdk==0.1.32"
        )

    def test_at_001_uv_lock_has_new_sdk_version(self):
        """AT-001: uv.lock contains SDK version 0.1.32."""
        lock_path = REPO_ROOT / "uv.lock"
        content = lock_path.read_text(encoding="utf-8")
        assert 'name = "github-copilot-sdk"' in content
        assert "0.1.32" in content, "uv.lock should contain SDK version 0.1.32"

    def test_at_001_installed_sdk_version(self):
        """AT-001: Installed SDK package is version 0.1.32."""
        version = importlib.metadata.version("github-copilot-sdk")
        assert version == "0.1.32", f"Expected SDK 0.1.32, got {version}"

    # ------------------------------------------------------------------
    # AT-002: All Tests Pass (meta-validation via imports)
    # ------------------------------------------------------------------
    def test_at_002_teambot_imports_successfully(self):
        """AT-002: TeamBot core modules import without errors."""
        import teambot
        import teambot.cli
        import teambot.copilot
        import teambot.copilot.sdk_client

        assert teambot is not None
        assert teambot.cli is not None
        assert teambot.copilot is not None

    def test_at_002_sdk_imports_successfully(self):
        """AT-002: SDK modules import without errors."""
        from copilot import CopilotClient
        from copilot.generated.session_events import SessionEventType

        assert CopilotClient is not None
        assert SessionEventType is not None

    # ------------------------------------------------------------------
    # AT-003: SDK Integration Tests Pass
    # ------------------------------------------------------------------
    def test_at_003_sdk_client_instantiates(self):
        """AT-003: CopilotSDKClient can be instantiated."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        client = CopilotSDKClient()
        assert client is not None
        assert client.is_available() is True
        assert client._started is False

    def test_at_003_sdk_client_error_defined(self):
        """AT-003: SDKClientError exception is properly defined."""
        from teambot.copilot.sdk_client import SDKClientError

        assert issubclass(SDKClientError, Exception)
        # Can instantiate with message
        error = SDKClientError("test error")
        assert str(error) == "test error"

    def test_at_003_session_event_types_exist(self):
        """AT-003: Required session event types exist in SDK."""
        from copilot.generated.session_events import SessionEventType

        # These are the event types TeamBot uses
        assert hasattr(SessionEventType, "ASSISTANT_MESSAGE_DELTA")
        assert hasattr(SessionEventType, "SESSION_IDLE")
        assert hasattr(SessionEventType, "SESSION_ERROR")
        assert hasattr(SessionEventType, "ABORT")

    # ------------------------------------------------------------------
    # AT-004: Linting Passes
    # ------------------------------------------------------------------
    def test_at_004_ruff_check_passes(self):
        """AT-004: ruff check . exits with code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, f"ruff check failed:\n{result.stdout}\n{result.stderr}"

    def test_at_004_ruff_format_check_passes(self):
        """AT-004: ruff format --check . exits with code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--check", "."],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, f"ruff format failed:\n{result.stdout}\n{result.stderr}"

    # ------------------------------------------------------------------
    # AT-005: CLI Starts Successfully
    # ------------------------------------------------------------------
    def test_at_005_cli_help_runs(self):
        """AT-005: teambot --help exits 0 and shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "teambot.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=30,
        )
        assert result.returncode == 0, f"CLI help failed:\n{result.stderr}"
        assert "TeamBot" in result.stdout, "Help should mention TeamBot"
        assert "usage:" in result.stdout.lower(), "Help should show usage"

    def test_at_005_cli_version_runs(self):
        """AT-005: teambot --version shows version 0.4.1."""
        result = subprocess.run(
            [sys.executable, "-m", "teambot.cli", "--version"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=30,
        )
        assert result.returncode == 0, f"CLI version failed:\n{result.stderr}"
        assert "0.4.1" in result.stdout, f"Version should be 0.4.1, got: {result.stdout}"

    # ------------------------------------------------------------------
    # AT-006: Version Bump Applied
    # ------------------------------------------------------------------
    def test_at_006_pyproject_version_bumped(self):
        """AT-006: pyproject.toml has version = "0.4.1"."""
        pyproject_path = REPO_ROOT / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        assert 'version = "0.4.1"' in content, 'pyproject.toml should have version = "0.4.1"'

    def test_at_006_init_version_bumped(self):
        """AT-006: src/teambot/__init__.py has __version__ = "0.4.1"."""
        init_path = REPO_ROOT / "src" / "teambot" / "__init__.py"
        content = init_path.read_text(encoding="utf-8")
        assert '__version__ = "0.4.1"' in content, '__init__.py should have __version__ = "0.4.1"'

    def test_at_006_versions_match(self):
        """AT-006: Versions in pyproject.toml and __init__.py match."""
        import teambot

        # Read pyproject.toml version
        pyproject_path = REPO_ROOT / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")

        # Extract version from pyproject.toml
        pyproject_version = None
        for line in content.split("\n"):
            if line.strip().startswith("version = "):
                pyproject_version = line.split('"')[1]
                break

        assert pyproject_version is not None, "Could not find 'version = ' in pyproject.toml"
        assert teambot.__version__ == pyproject_version, (
            f"Version mismatch: __init__.py has {teambot.__version__}, "
            f"pyproject.toml has {pyproject_version}"
        )

    def test_at_006_python_requirement_updated(self):
        """AT-006: Python requirement updated to >=3.11."""
        pyproject_path = REPO_ROOT / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        assert 'requires-python = ">=3.11"' in content, (
            'pyproject.toml should have requires-python = ">=3.11"'
        )
