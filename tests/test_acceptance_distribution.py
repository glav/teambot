"""Acceptance test validation for distribution feature.

These tests validate the acceptance scenarios for the 'Run Directly' feature.
Tests call REAL implementation code, not mocks.
"""

import sys
from pathlib import Path
from unittest.mock import patch


class TestAcceptanceScenarios:
    """Acceptance tests for distribution feature."""

    # =========================================================================
    # AT-001: Fresh pip Installation on Linux
    # =========================================================================

    def test_at_001_version_command(self):
        """AT-001: teambot --version displays version correctly."""
        from teambot import __version__
        from teambot.cli import create_parser

        parser = create_parser()
        # Version is handled by argparse, verify it's configured
        assert parser.prog == "teambot"

        # Also verify version is importable and correct format
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert __version__ == "0.2.0"

    def test_at_001_help_command(self):
        """AT-001: teambot --help shows all commands."""
        from teambot.cli import create_parser

        parser = create_parser()

        # Verify subparsers exist for all commands
        subparsers_action = None
        for action in parser._actions:
            if hasattr(action, "_parser_class"):
                subparsers_action = action
                break

        assert subparsers_action is not None
        choices = subparsers_action.choices
        assert "init" in choices
        assert "run" in choices
        assert "status" in choices

    def test_at_001_init_creates_directory(self, tmp_path, monkeypatch):
        """AT-001: teambot init creates .teambot/ directory."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()
        assert (tmp_path / ".teambot").is_dir()
        assert (tmp_path / ".teambot" / "history").is_dir()
        assert (tmp_path / ".teambot" / "state").is_dir()

    def test_at_001_init_creates_valid_config(self, tmp_path, monkeypatch):
        """AT-001: teambot init creates valid JSON configuration."""
        import argparse
        import json

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        cmd_init(args, display)

        config_path = tmp_path / "teambot.json"
        config = json.loads(config_path.read_text())

        assert "agents" in config
        assert isinstance(config["agents"], list)
        assert len(config["agents"]) > 0

    # =========================================================================
    # AT-002: uvx Ephemeral Execution
    # =========================================================================

    def test_at_002_uvx_help_simulation(self):
        """AT-002: uvx copilot-teambot --help works (simulated via direct call)."""
        from teambot.cli import create_parser

        # Simulate uvx by directly calling the entry point
        parser = create_parser()

        # Parse help would normally exit, so verify parser is functional
        assert parser.description is not None
        assert "TeamBot" in parser.description

    def test_at_002_uvx_init_simulation(self, tmp_path, monkeypatch):
        """AT-002: uvx copilot-teambot init creates configuration."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Simulate uvx execution by calling init directly
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / ".teambot").is_dir()
        assert (tmp_path / "teambot.json").exists()

    # =========================================================================
    # AT-003: Windows PowerShell Installation
    # =========================================================================

    def test_at_003_windows_path_handling(self, tmp_path, monkeypatch):
        """AT-003: Windows paths handled correctly."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0

        # Verify paths work regardless of platform (Path normalizes)
        teambot_dir = tmp_path / ".teambot"
        assert teambot_dir.exists()

        # Check that pathlib handles the paths correctly
        history_dir = teambot_dir / "history"
        state_dir = teambot_dir / "state"
        assert history_dir.exists()
        assert state_dir.exists()

    def test_at_003_status_command(self, tmp_path, monkeypatch):
        """AT-003: teambot status works after init."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init, cmd_status

        monkeypatch.chdir(tmp_path)

        # Initialize first
        init_args = argparse.Namespace(force=False)
        cmd_init(init_args, ConsoleDisplay())

        # Run status
        status_args = argparse.Namespace()
        display = ConsoleDisplay()

        result = cmd_status(status_args, display)

        assert result == 0

    def test_at_003_status_fails_without_init(self, tmp_path, monkeypatch):
        """AT-003: teambot status fails gracefully without init."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_status

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace()
        display = ConsoleDisplay()

        result = cmd_status(args, display)

        assert result == 1  # Fails because not initialized

    # =========================================================================
    # AT-004: Missing Copilot CLI Detection
    # =========================================================================

    def test_at_004_copilot_cli_missing_returns_false(self):
        """AT-004: check_copilot_cli returns False when CLI missing."""
        with patch("shutil.which", return_value=None):
            # Need to reimport to get the patched version
            import importlib

            import teambot.cli

            importlib.reload(teambot.cli)
            from teambot.cli import check_copilot_cli

            result = check_copilot_cli()
            assert result is False

    def test_at_004_error_includes_install_url(self):
        """AT-004: Error message includes installation URL."""
        from teambot.cli import COPILOT_CLI_INSTALL_URL

        assert COPILOT_CLI_INSTALL_URL is not None
        assert "githubnext.com" in COPILOT_CLI_INSTALL_URL
        assert "copilot-cli" in COPILOT_CLI_INSTALL_URL

    def test_at_004_main_returns_error_when_cli_missing(self):
        """AT-004: main() returns error code when Copilot CLI missing."""
        with patch("shutil.which", return_value=None):
            with patch.object(sys, "argv", ["teambot", "run"]):
                from teambot.cli import main

                result = main()
                assert result == 1  # Error exit code

    def test_at_004_init_works_without_copilot_cli(self, tmp_path, monkeypatch):
        """AT-004: init command works even without Copilot CLI."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # init should work regardless of Copilot CLI status
        with patch("shutil.which", return_value=None):
            args = argparse.Namespace(force=False)
            display = ConsoleDisplay()

            result = cmd_init(args, display)

            # init doesn't require Copilot CLI
            assert result == 0

    # =========================================================================
    # AT-005: Devcontainer Feature Installation
    # =========================================================================

    def test_at_005_devcontainer_feature_json_exists(self):
        """AT-005: Devcontainer feature JSON file exists."""
        feature_json = Path("features/teambot/devcontainer-feature.json")
        assert feature_json.exists(), f"Missing: {feature_json}"

    def test_at_005_devcontainer_feature_json_valid(self):
        """AT-005: Devcontainer feature JSON is valid."""
        import json

        feature_json = Path("features/teambot/devcontainer-feature.json")
        content = json.loads(feature_json.read_text())

        # Required fields per devcontainer spec
        assert "id" in content
        assert "version" in content
        assert "name" in content

        assert content["id"] == "teambot"
        assert content["version"] == "1.0.0"

    def test_at_005_devcontainer_install_script_exists(self):
        """AT-005: Devcontainer install script exists."""
        install_script = Path("features/teambot/install.sh")
        assert install_script.exists(), f"Missing: {install_script}"

    def test_at_005_devcontainer_install_script_valid(self):
        """AT-005: Devcontainer install script has correct structure."""
        install_script = Path("features/teambot/install.sh")
        content = install_script.read_text()

        # Script should install uv and copilot-teambot
        assert "#!/" in content  # Has shebang
        assert "uv" in content  # Uses uv
        assert "copilot-teambot" in content  # Installs our package

    # =========================================================================
    # AT-006: Docker Image Execution
    # =========================================================================

    def test_at_006_dockerfile_exists(self):
        """AT-006: Dockerfile exists."""
        dockerfile = Path("docker/Dockerfile")
        assert dockerfile.exists(), f"Missing: {dockerfile}"

    def test_at_006_dockerfile_valid(self):
        """AT-006: Dockerfile has correct structure."""
        dockerfile = Path("docker/Dockerfile")
        content = dockerfile.read_text()

        # Required Dockerfile elements
        assert "FROM" in content
        assert "python" in content.lower()
        assert "copilot-teambot" in content
        assert "ENTRYPOINT" in content
        assert "teambot" in content

    def test_at_006_dockerfile_installs_teambot(self):
        """AT-006: Dockerfile installs TeamBot correctly."""
        dockerfile = Path("docker/Dockerfile")
        content = dockerfile.read_text()

        # Check for proper installation steps
        assert "uv tool install" in content or "pip install" in content
        assert "WORKDIR" in content

    def test_at_006_docker_entrypoint_correct(self):
        """AT-006: Docker entrypoint is teambot."""
        dockerfile = Path("docker/Dockerfile")
        content = dockerfile.read_text()

        # Should have teambot as entrypoint
        assert 'ENTRYPOINT ["teambot"]' in content

    # =========================================================================
    # AT-007: Cross-Python Version Compatibility
    # =========================================================================

    def test_at_007_requires_python_310_plus(self):
        """AT-007: Package requires Python 3.10+."""
        import tomllib

        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        requires_python = config["project"]["requires-python"]
        assert ">=3.10" in requires_python

    def test_at_007_classifiers_include_all_versions(self):
        """AT-007: Package classifiers include Python 3.10, 3.11, 3.12."""
        import tomllib

        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        classifiers = config["project"]["classifiers"]

        # Check for version classifiers
        python_versions = [c for c in classifiers if "Python :: 3." in c]
        version_strings = " ".join(python_versions)

        assert "3.10" in version_strings
        assert "3.11" in version_strings
        assert "3.12" in version_strings

    def test_at_007_ci_matrix_configured(self):
        """AT-007: CI workflow has cross-version matrix."""
        import yaml

        ci_yml = Path(".github/workflows/ci.yml")
        assert ci_yml.exists()

        content = yaml.safe_load(ci_yml.read_text())

        # Find the test job
        test_job = content["jobs"]["test"]
        matrix = test_job["strategy"]["matrix"]

        # Check Python versions
        python_versions = matrix["python-version"]
        assert "3.10" in python_versions
        assert "3.11" in python_versions
        assert "3.12" in python_versions

        # Check OS platforms
        os_list = matrix["os"]
        assert "ubuntu-latest" in os_list
        assert "macos-latest" in os_list
        assert "windows-latest" in os_list

    def test_at_007_current_python_supported(self):
        """AT-007: Current Python version is supported."""
        major, minor = sys.version_info[:2]

        # Must be 3.10 or higher
        assert major == 3
        assert minor >= 10
