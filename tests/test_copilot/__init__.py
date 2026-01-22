"""Tests for Copilot CLI client."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from teambot.copilot.client import CopilotClient, CopilotConfig, CopilotResult


class TestCopilotResult:
    """Tests for CopilotResult dataclass."""

    def test_success_result(self):
        """Test creating a successful result."""
        result = CopilotResult(
            success=True,
            output="Task completed",
            exit_code=0,
            prompt="Test prompt",
        )
        assert result.success is True
        assert result.output == "Task completed"
        assert result.error is None
        assert result.exit_code == 0

    def test_failure_result(self):
        """Test creating a failure result."""
        result = CopilotResult(
            success=False,
            output="",
            error="Command failed",
            exit_code=1,
            prompt="Test prompt",
        )
        assert result.success is False
        assert result.error == "Command failed"
        assert result.exit_code == 1


class TestCopilotConfig:
    """Tests for CopilotConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CopilotConfig()
        assert config.allow_all_tools is True
        assert config.allow_all_paths is False
        assert config.additional_dirs == []
        assert config.model is None
        assert config.timeout == 300

    def test_custom_config(self):
        """Test custom configuration."""
        config = CopilotConfig(
            allow_all_tools=False,
            allow_all_paths=True,
            additional_dirs=["/tmp", "/home"],
            model="gpt-5",
            timeout=600,
        )
        assert config.allow_all_tools is False
        assert config.allow_all_paths is True
        assert config.additional_dirs == ["/tmp", "/home"]
        assert config.model == "gpt-5"
        assert config.timeout == 600


class TestCopilotClient:
    """Tests for CopilotClient class."""

    @patch("shutil.which")
    def test_copilot_available(self, mock_which):
        """Test checking if Copilot CLI is available."""
        mock_which.return_value = "/usr/local/bin/copilot"
        client = CopilotClient()
        assert client.is_available() is True

    @patch("shutil.which")
    def test_copilot_not_available(self, mock_which):
        """Test when Copilot CLI is not available."""
        mock_which.return_value = None
        client = CopilotClient()
        assert client.is_available() is False

    @patch("shutil.which")
    def test_copilot_path_property(self, mock_which):
        """Test copilot_path property."""
        mock_which.return_value = "/usr/local/bin/copilot"
        client = CopilotClient()
        assert client.copilot_path == "/usr/local/bin/copilot"

    @patch("shutil.which")
    def test_copilot_path_not_found_raises(self, mock_which):
        """Test copilot_path raises when not found."""
        mock_which.return_value = None
        client = CopilotClient()
        with pytest.raises(RuntimeError, match="Copilot CLI not found"):
            _ = client.copilot_path

    @patch("shutil.which")
    def test_build_command_basic(self, mock_which):
        """Test building basic command."""
        mock_which.return_value = "/usr/local/bin/copilot"
        client = CopilotClient()
        cmd = client._build_command("Test prompt")

        assert cmd[0] == "/usr/local/bin/copilot"
        assert cmd[1] == "-p"
        assert cmd[2] == "Test prompt"
        assert "--allow-all-tools" in cmd

    @patch("shutil.which")
    def test_build_command_with_model(self, mock_which):
        """Test building command with model specified."""
        mock_which.return_value = "/usr/local/bin/copilot"
        config = CopilotConfig(model="gpt-5")
        client = CopilotClient(config=config)
        cmd = client._build_command("Test prompt")

        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "gpt-5"

    @patch("shutil.which")
    def test_build_command_with_dirs(self, mock_which):
        """Test building command with additional directories."""
        mock_which.return_value = "/usr/local/bin/copilot"
        config = CopilotConfig(additional_dirs=["/tmp", "/home"])
        client = CopilotClient(config=config)
        cmd = client._build_command("Test prompt")

        assert cmd.count("--add-dir") == 2
        assert "/tmp" in cmd
        assert "/home" in cmd

    @patch("shutil.which")
    def test_build_command_allow_all_paths(self, mock_which):
        """Test building command with allow_all_paths."""
        mock_which.return_value = "/usr/local/bin/copilot"
        config = CopilotConfig(allow_all_paths=True)
        client = CopilotClient(config=config)
        cmd = client._build_command("Test prompt")

        assert "--allow-all-paths" in cmd

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_execute_success(self, mock_run, mock_which):
        """Test successful execution."""
        mock_which.return_value = "/usr/local/bin/copilot"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success output",
            stderr="",
        )

        client = CopilotClient()
        result = client.execute("Test task")

        assert result.success is True
        assert result.output == "Success output"
        assert result.exit_code == 0
        mock_run.assert_called_once()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_execute_failure(self, mock_run, mock_which):
        """Test failed execution."""
        mock_which.return_value = "/usr/local/bin/copilot"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error occurred",
        )

        client = CopilotClient()
        result = client.execute("Test task")

        assert result.success is False
        assert result.error == "Error occurred"
        assert result.exit_code == 1

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_execute_with_context(self, mock_run, mock_which):
        """Test execution with context."""
        mock_which.return_value = "/usr/local/bin/copilot"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success",
            stderr="",
        )

        client = CopilotClient()
        result = client.execute("Test task", context="Additional context")

        assert result.success is True
        assert "Additional context" in result.prompt
        assert "Test task" in result.prompt

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_execute_timeout(self, mock_run, mock_which):
        """Test execution timeout."""
        mock_which.return_value = "/usr/local/bin/copilot"
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="copilot", timeout=300, stdout=b"partial"
        )

        client = CopilotClient()
        result = client.execute("Test task")

        assert result.success is False
        assert "Timeout" in result.error

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_execute_file_not_found(self, mock_run, mock_which):
        """Test execution when command not found."""
        mock_which.return_value = "/usr/local/bin/copilot"
        mock_run.side_effect = FileNotFoundError()

        client = CopilotClient()
        result = client.execute("Test task")

        assert result.success is False
        assert "not found" in result.error.lower()

    @patch("shutil.which")
    def test_working_dir_default(self, mock_which):
        """Test default working directory."""
        mock_which.return_value = "/usr/local/bin/copilot"
        client = CopilotClient()
        assert client.working_dir == Path.cwd()

    @patch("shutil.which")
    def test_working_dir_custom(self, mock_which, tmp_path):
        """Test custom working directory."""
        mock_which.return_value = "/usr/local/bin/copilot"
        client = CopilotClient(working_dir=tmp_path)
        assert client.working_dir == tmp_path
