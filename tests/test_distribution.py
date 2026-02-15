"""Tests for package distribution and installation."""

import sys

if sys.version_info >= (3, 11):  # noqa: UP036
    import tomllib
else:
    import tomli as tomllib
from pathlib import Path
from unittest.mock import patch


class TestPackageMetadata:
    """Tests for package configuration."""

    def test_pyproject_has_required_fields(self):
        """Verify pyproject.toml has all required fields."""
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        assert config["project"]["name"] == "teambot"
        assert "version" in config["project"]
        assert "description" in config["project"]
        assert config["project"]["requires-python"] == ">=3.10"

    def test_entry_point_defined(self):
        """Verify CLI entry point is defined."""
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        scripts = config["project"]["scripts"]
        assert "teambot" in scripts
        assert scripts["teambot"] == "teambot.cli:main"


class TestCopilotCLIDetection:
    """Tests for Copilot CLI detection (FR-006)."""

    def test_copilot_cli_present_returns_true(self):
        """When Copilot CLI is installed, check returns True."""
        with patch("shutil.which", return_value="/usr/local/bin/copilot"):
            from teambot.cli import check_copilot_cli

            result = check_copilot_cli()
            assert result is True

    def test_copilot_cli_missing_returns_false(self):
        """When Copilot CLI is missing, check returns False."""
        with patch("shutil.which", return_value=None):
            # Need to reimport to get the patched version
            import importlib

            import teambot.cli

            importlib.reload(teambot.cli)
            from teambot.cli import check_copilot_cli

            result = check_copilot_cli()
            assert result is False

    def test_copilot_cli_url_constant_defined(self):
        """Verify COPILOT_CLI_INSTALL_URL is defined."""
        from teambot.cli import COPILOT_CLI_INSTALL_URL

        assert COPILOT_CLI_INSTALL_URL is not None
        assert "githubnext.com" in COPILOT_CLI_INSTALL_URL

    def test_main_checks_copilot_cli_for_run_command(self):
        """Verify main() checks for Copilot CLI before run command."""
        import sys

        with patch("shutil.which", return_value=None):
            with patch.object(sys, "argv", ["teambot", "run"]):
                from teambot.cli import main

                # Should return 1 when Copilot CLI is missing
                result = main()
                assert result == 1


class TestPackageStructure:
    """Tests for package structure validity."""

    def test_src_layout_exists(self):
        """Verify src/teambot package exists."""
        assert Path("src/teambot").is_dir()
        assert Path("src/teambot/__init__.py").is_file()

    def test_cli_module_exists(self):
        """Verify CLI module exists."""
        assert Path("src/teambot/cli.py").is_file()

    def test_version_importable(self):
        """Verify version can be imported."""
        from teambot import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)


class TestDistributionArtifacts:
    """Tests for distribution-related files."""

    def test_readme_exists(self):
        """Verify README.md exists for PyPI description."""
        assert Path("README.md").is_file()

    def test_readme_has_installation_section(self):
        """Verify README has installation instructions."""
        content = Path("README.md").read_text(encoding="utf-8")
        assert "## Installation" in content
        assert "uv" in content  # Uses uv-based installation

    def test_installation_guide_exists(self):
        """Verify installation guide exists."""
        assert Path("docs/guides/installation.md").is_file()

    def test_dockerfile_exists(self):
        """Verify Dockerfile exists for container distribution."""
        assert Path("docker/Dockerfile").is_file()

    def test_devcontainer_feature_exists(self):
        """Verify devcontainer feature files exist."""
        assert Path("features/teambot/devcontainer-feature.json").is_file()
        assert Path("features/teambot/install.sh").is_file()
