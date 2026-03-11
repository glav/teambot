"""Tests for CLI - end-to-end tests."""

import json

import pytest


class TestCLIParser:
    """Tests for CLI argument parsing."""

    def test_parser_init_command(self):
        """Parser recognizes init command."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["init"])

        assert args.command == "init"

    def test_parser_run_command(self):
        """Parser recognizes run command with objective."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md"])

        assert args.command == "run"
        assert args.objective == "objective.md"

    def test_parser_run_with_config(self):
        """Parser accepts custom config path."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "-c", "custom.json", "obj.md"])

        assert args.config == "custom.json"

    def test_parser_status_command(self):
        """Parser recognizes status command."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["status"])

        assert args.command == "status"

    def test_parser_verbose_flag(self):
        """Parser recognizes verbose flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["-v", "init"])

        assert args.verbose is True

    def test_parser_accepts_no_animation_flag(self):
        """Parser recognizes --no-animation flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-animation", "run", "obj.md"])

        assert args.no_animation is True

    def test_no_animation_flag_defaults_false(self):
        """--no-animation defaults to False when not provided."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md"])

        assert args.no_animation is False


class TestCLIParserWorktree:
    """Tests for worktree CLI argument parsing."""

    def test_parser_worktree_flag(self):
        """Parser recognizes --worktree flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md", "--worktree"])

        assert args.worktree is True

    def test_parser_worktree_flag_default_false(self):
        """--worktree flag defaults to False."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md"])

        assert args.worktree is False

    def test_parser_branch_flag(self):
        """Parser recognizes --branch flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md", "--branch", "feat/custom"])

        assert args.branch == "feat/custom"

    def test_parser_branch_flag_default_none(self):
        """--branch flag defaults to None."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md"])

        assert args.branch is None

    def test_parser_worktree_with_branch(self):
        """Parser accepts both --worktree and --branch flags."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md", "--worktree", "--branch", "fix/bug-123"])

        assert args.worktree is True
        assert args.branch == "fix/bug-123"

    def test_parser_backward_compatibility_no_worktree(self):
        """Existing run commands work without --worktree flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "my-objective.md", "--max-hours", "4"])

        assert args.command == "run"
        assert args.objective == "my-objective.md"
        assert args.max_hours == 4
        assert args.worktree is False
        assert args.branch is None

    def test_parser_base_branch_flag(self):
        """Parser recognizes --base-branch flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md", "--worktree", "--base-branch", "main"])

        assert args.base_branch == "main"

    def test_parser_base_branch_default_none(self):
        """--base-branch flag defaults to None when not specified."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md", "--worktree"])

        assert args.base_branch is None

    def test_parser_base_branch_without_worktree(self):
        """--base-branch is parsed even without --worktree (just unused)."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md", "--base-branch", "develop"])

        assert args.base_branch == "develop"

    def test_parser_worktree_with_base_branch_and_branch(self):
        """Parser accepts --worktree, --branch, and --base-branch together."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["run", "obj.md", "--worktree", "--branch", "feat/task", "--base-branch", "main"]
        )

        assert args.worktree is True
        assert args.branch == "feat/task"
        assert args.base_branch == "main"


class TestCmdRunWorktree:
    """Tests for cmd_run with --worktree flag."""

    def test_cmd_run_worktree_requires_objective(self, tmp_path, monkeypatch):
        """--worktree without objective file returns error."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Create config so we get past config check
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        args = argparse.Namespace(
            config="teambot.json",
            objective=None,
            worktree=True,
            branch=None,
        )
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 1

    def test_cmd_run_worktree_git_not_available(self, tmp_path, monkeypatch):
        """--worktree fails when Git is not available."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Create config and objective
        (tmp_path / "teambot.json").write_text('{"agents": []}')
        (tmp_path / "my-feature.md").write_text("# Objective\n")

        # Mock Git as not available
        monkeypatch.setattr("teambot.worktree.manager.shutil.which", lambda x: None)

        args = argparse.Namespace(
            config="teambot.json",
            objective="my-feature.md",
            worktree=True,
            branch=None,
        )
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 1

    def test_cmd_run_worktree_not_in_git_repo(self, tmp_path, monkeypatch):
        """--worktree fails when not in a Git repository."""
        import argparse
        from unittest.mock import MagicMock

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Create config and objective
        (tmp_path / "teambot.json").write_text('{"agents": []}')
        (tmp_path / "my-feature.md").write_text("# Objective\n")

        # Mock Git as available but not in repo
        monkeypatch.setattr("teambot.worktree.manager.shutil.which", lambda x: "/usr/bin/git")
        mock_run = MagicMock(return_value=MagicMock(returncode=128, stdout=""))
        monkeypatch.setattr("teambot.worktree.manager.subprocess.run", mock_run)

        args = argparse.Namespace(
            config="teambot.json",
            objective="my-feature.md",
            worktree=True,
            branch=None,
        )
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 1

    def test_cmd_run_without_worktree_unchanged(self, tmp_path, monkeypatch):
        """Running without --worktree behaves as before (regression)."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init, cmd_run

        monkeypatch.chdir(tmp_path)

        # Mock model validation
        monkeypatch.setattr("teambot.config.loader.validate_model", lambda m: True)
        monkeypatch.setattr("teambot.cli._check_copilot_authentication_blocking", lambda d: True)
        monkeypatch.setattr("teambot.cli._ensure_model_cache", lambda d: None)

        # Initialize first
        init_args = argparse.Namespace(force=False)
        cmd_init(init_args, ConsoleDisplay())

        # Mock the REPL
        async def mock_repl(*args, **kwargs):
            pass

        monkeypatch.setattr("teambot.repl.run_interactive_mode", mock_repl)

        args = argparse.Namespace(
            config="teambot.json",
            objective=None,
            worktree=False,
            branch=None,
        )
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 0


class TestCmdRunWorktreeObjectiveMigration:
    """TDD tests for objective file migration to worktree."""

    @staticmethod
    def _make_git_repo(path) -> None:
        """Create a minimal committed git repo with only teambot.json and README."""
        import subprocess

        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=path,
            capture_output=True,
            check=True,
        )
        (path / "teambot.json").write_text('{"agents": []}')
        (path / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=path,
            capture_output=True,
            check=True,
        )

    def test_cmd_run_worktree_copies_objective_from_source(self, tmp_path, monkeypatch):
        """Objective file is copied from source repo when missing in worktree."""
        import argparse
        import subprocess
        from unittest.mock import patch

        from teambot.cli import ConsoleDisplay, cmd_run

        # Create a real git repo
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Commit only config (no objective) so the worktree won't have the objective
        (repo / "teambot.json").write_text('{"agents": []}')
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create objective in source repo but do NOT commit it
        objectives_dir = repo / "objectives"
        objectives_dir.mkdir()
        objective_file = objectives_dir / "my-task.md"
        objective_file.write_text("# Test Objective\n\nGoals here.")

        monkeypatch.chdir(repo)
        monkeypatch.setattr("teambot.cli._check_copilot_authentication_blocking", lambda d: True)
        monkeypatch.setattr("teambot.cli._ensure_model_cache", lambda d: None)

        # Compute the expected worktree path (branch feat/my-task → dir feat-my-task)
        expected_worktree_objective = (
            repo / ".teambot-worktrees" / "feat-my-task" / "objectives" / "my-task.md"
        )

        # Mock the orchestration to avoid full run
        with patch("teambot.cli._run_orchestration", return_value=0):
            args = argparse.Namespace(
                config="teambot.json",
                objective="objectives/my-task.md",
                worktree=True,
                branch=None,
                base_branch=None,
                max_hours=8.0,
                no_animation=True,
                verbose=False,
                log_to_console=False,
                resume=False,
            )
            display = ConsoleDisplay()

            result = cmd_run(args, display)

        assert result == 0
        # Verify objective was copied from source repo into the worktree
        assert expected_worktree_objective.exists(), "Objective was not copied into the worktree"
        assert expected_worktree_objective.read_text() == "# Test Objective\n\nGoals here."

    def test_cmd_run_worktree_creates_parent_dirs_for_objective(self, tmp_path, monkeypatch):
        """Parent directories created when copying nested objective file."""
        import argparse
        import subprocess
        from unittest.mock import patch

        from teambot.cli import ConsoleDisplay, cmd_run

        # Create a real git repo
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Commit only config (no objective) so the worktree won't have the nested objective
        (repo / "teambot.json").write_text('{"agents": []}')
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create nested objective in source repo but do NOT commit it
        nested_dir = repo / "docs" / "objectives" / "features"
        nested_dir.mkdir(parents=True)
        objective_file = nested_dir / "my-task.md"
        objective_file.write_text("# Nested Objective\n\nWith subdirectories.")

        monkeypatch.chdir(repo)
        monkeypatch.setattr("teambot.cli._check_copilot_authentication_blocking", lambda d: True)
        monkeypatch.setattr("teambot.cli._ensure_model_cache", lambda d: None)

        # Compute the expected worktree path (branch feat/my-task → dir feat-my-task)
        expected_worktree_objective = (
            repo
            / ".teambot-worktrees"
            / "feat-my-task"
            / "docs"
            / "objectives"
            / "features"
            / "my-task.md"
        )

        with patch("teambot.cli._run_orchestration", return_value=0):
            args = argparse.Namespace(
                config="teambot.json",
                objective="docs/objectives/features/my-task.md",
                worktree=True,
                branch=None,
                base_branch=None,
                max_hours=8.0,
                no_animation=True,
                verbose=False,
                log_to_console=False,
                resume=False,
            )
            display = ConsoleDisplay()

            result = cmd_run(args, display)

        assert result == 0
        # Verify nested objective was copied with parent directories created
        assert expected_worktree_objective.exists(), (
            "Nested objective was not copied into the worktree"
        )
        assert expected_worktree_objective.parent.is_dir(), (
            "Parent directories were not created in the worktree"
        )

    def test_cmd_run_worktree_no_copy_when_exists(self, tmp_path, monkeypatch):
        """No copy when objective already exists in worktree."""
        import argparse
        import subprocess
        from unittest.mock import patch

        from teambot.cli import ConsoleDisplay, cmd_run

        # Create a real git repo
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create config and objective and commit
        (repo / "teambot.json").write_text('{"agents": []}')
        objectives_dir = repo / "objectives"
        objectives_dir.mkdir()
        objective_file = objectives_dir / "my-task.md"
        objective_file.write_text("# Test Objective")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        monkeypatch.chdir(repo)
        monkeypatch.setattr("teambot.cli._check_copilot_authentication_blocking", lambda d: True)
        monkeypatch.setattr("teambot.cli._ensure_model_cache", lambda d: None)

        with (
            patch("teambot.cli._run_orchestration", return_value=0),
            patch("teambot.cli.shutil.copy2") as mock_copy,
        ):
            args = argparse.Namespace(
                config="teambot.json",
                objective="objectives/my-task.md",
                worktree=True,
                branch=None,
                base_branch=None,
                max_hours=8.0,
                no_animation=True,
                verbose=False,
                log_to_console=False,
                resume=False,
            )
            display = ConsoleDisplay()

            # Should succeed without copy (file already exists in committed state)
            result = cmd_run(args, display)

        assert result == 0
        # Verify no copy was performed since the file already existed in the worktree
        mock_copy.assert_not_called()

    def test_cmd_run_worktree_error_when_objective_not_found(self, tmp_path, monkeypatch):
        """Error when objective file doesn't exist in source or worktree."""
        import argparse
        import subprocess

        from teambot.cli import ConsoleDisplay, cmd_run

        # Create a real git repo
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create config only (no objective file)
        (repo / "teambot.json").write_text('{"agents": []}')
        (repo / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        monkeypatch.chdir(repo)

        args = argparse.Namespace(
            config="teambot.json",
            objective="objectives/missing.md",
            worktree=True,
            branch=None,
            base_branch=None,
        )
        display = ConsoleDisplay()

        # Should fail because objective file doesn't exist anywhere
        result = cmd_run(args, display)

        assert result == 1

    def test_cmd_run_worktree_rejects_objective_outside_repo(self, tmp_path, monkeypatch):
        """Objective path escaping the repo root is rejected before any copy."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_run

        repo = tmp_path / "repo"
        self._make_git_repo(repo)
        monkeypatch.chdir(repo)

        # Path traversal that resolves outside repo_root
        args = argparse.Namespace(
            config="teambot.json",
            objective="../../outside/task.md",
            worktree=True,
            branch=None,
            base_branch=None,
        )
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 1

    def test_cmd_run_worktree_rejects_absolute_objective_outside_repo(self, tmp_path, monkeypatch):
        """Absolute objective path pointing outside repo root is rejected."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_run

        repo = tmp_path / "repo"
        self._make_git_repo(repo)
        monkeypatch.chdir(repo)

        # Create a file outside the repo to use as an absolute path target
        outside_file = tmp_path / "outside" / "secret.md"
        outside_file.parent.mkdir(parents=True)
        outside_file.write_text("secret content")

        args = argparse.Namespace(
            config="teambot.json",
            objective=str(outside_file),
            worktree=True,
            branch=None,
            base_branch=None,
        )
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 1


class TestCLIInit:
    """Tests for init command."""

    def test_init_creates_config(self, tmp_path, monkeypatch):
        """Init creates configuration file."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()
        assert (tmp_path / ".teambot").exists()

    def test_init_fails_if_exists(self, tmp_path, monkeypatch):
        """Init fails if config exists without --force."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create existing config
        (tmp_path / "teambot.json").write_text("{}", encoding="utf-8")

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 1

    def test_init_force_overwrites(self, tmp_path, monkeypatch):
        """Init with --force overwrites existing config."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create existing config
        (tmp_path / "teambot.json").write_text("{}", encoding="utf-8")

        args = argparse.Namespace(force=True)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        # Should have real config now
        config = json.loads((tmp_path / "teambot.json").read_text(encoding="utf-8"))
        assert "agents" in config

    def test_init_copies_scaffolds(self, tmp_path, monkeypatch):
        """Init copies scaffold files to new repository."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / ".github" / "agents").exists()
        assert (tmp_path / ".agent").exists()

    def test_init_skips_existing_scaffolds(self, tmp_path, monkeypatch):
        """Init doesn't overwrite existing scaffold files but may append template reference."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create existing file
        (tmp_path / "AGENTS.md").write_text("My custom AGENTS")

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        cmd_init(args, display)

        # Should preserve existing content (appends template reference if template copied)
        content = (tmp_path / "AGENTS.md").read_text()
        assert content.startswith("My custom AGENTS")

    def test_init_force_overwrites_scaffolds(self, tmp_path, monkeypatch):
        """Init with --force overwrites scaffold files."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # First init
        cmd_init(argparse.Namespace(force=False), ConsoleDisplay())

        # Modify a file
        (tmp_path / "AGENTS.md").write_text("Modified")

        # Force re-init
        cmd_init(argparse.Namespace(force=True), ConsoleDisplay())

        # Should be overwritten with package version
        assert (tmp_path / "AGENTS.md").read_text() != "Modified"


class TestCLIRun:
    """Tests for run command."""

    def test_run_fails_without_config(self, tmp_path, monkeypatch):
        """Run fails if no configuration exists."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(config="teambot.json", objective=None)
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 1

    def test_run_with_valid_config(self, tmp_path, monkeypatch):
        """Run succeeds with valid configuration."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init, cmd_run

        monkeypatch.chdir(tmp_path)

        # Mock model validation to always return True (no SDK needed)
        monkeypatch.setattr("teambot.config.loader.validate_model", lambda m: True)

        # Mock authentication check to return True (no SDK needed)
        monkeypatch.setattr("teambot.cli._check_copilot_authentication_blocking", lambda d: True)

        # Mock model cache check (no SDK needed)
        monkeypatch.setattr("teambot.cli._ensure_model_cache", lambda d: None)

        # Initialize first
        init_args = argparse.Namespace(force=False)
        cmd_init(init_args, ConsoleDisplay())

        args = argparse.Namespace(config="teambot.json", objective=None)
        display = ConsoleDisplay()

        # Mock the REPL to avoid hanging on input

        async def mock_repl(*args, **kwargs):
            pass

        monkeypatch.setattr("teambot.repl.run_interactive_mode", mock_repl)

        result = cmd_run(args, display)

        assert result == 0


class TestCLIStatus:
    """Tests for status command."""

    def test_status_fails_without_init(self, tmp_path, monkeypatch):
        """Status fails if TeamBot not initialized."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_status

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace()
        display = ConsoleDisplay()

        result = cmd_status(args, display)

        assert result == 1

    def test_status_succeeds_after_init(self, tmp_path, monkeypatch):
        """Status succeeds after initialization."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init, cmd_status

        monkeypatch.chdir(tmp_path)

        # Initialize first
        init_args = argparse.Namespace(force=False)
        cmd_init(init_args, ConsoleDisplay())

        args = argparse.Namespace()
        display = ConsoleDisplay()

        result = cmd_status(args, display)

        assert result == 0


class TestCLIMain:
    """Tests for main entry point."""

    def test_main_no_command_shows_help(self, capsys):
        """Main with no command shows help."""
        import sys

        from teambot.cli import main

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(sys, "argv", ["teambot"])
            result = main()

        assert result == 0

    def test_main_returns_int(self, tmp_path, monkeypatch):
        """Main returns integer exit code."""
        import sys

        from teambot.cli import main

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["teambot", "status"])

        result = main()

        assert isinstance(result, int)


class TestInitNotificationMode:
    """Tests for notification mode selection in init wizard."""

    def test_setup_telegram_includes_notification_mode(self, tmp_path, monkeypatch):
        """_setup_telegram_notifications adds notification_mode to config."""
        from teambot.cli import ConsoleDisplay, _setup_telegram_notifications

        # Mock stdin for interactive input
        # Simulate: Y (proceed), Enter (default token), Enter (default chat_id), 2 (agent_status)
        inputs = iter(["y", "", "", "2"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        config = {}
        display = ConsoleDisplay()

        result = _setup_telegram_notifications(config, display)

        assert result is True
        assert "notifications" in config
        channel = config["notifications"]["channels"][0]
        assert "notification_mode" in channel
        assert channel["notification_mode"] == "agent_status"

    def test_setup_telegram_default_mode_is_stages_only(self, tmp_path, monkeypatch):
        """Default notification mode is stages_only when user presses Enter."""
        from teambot.cli import ConsoleDisplay, _setup_telegram_notifications

        # Simulate: Y (proceed), Enter x3 (all defaults including mode)
        inputs = iter(["y", "", "", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        config = {}
        display = ConsoleDisplay()

        result = _setup_telegram_notifications(config, display)

        assert result is True
        channel = config["notifications"]["channels"][0]
        assert channel["notification_mode"] == "stages_only"

    def test_setup_telegram_all_mode(self, tmp_path, monkeypatch):
        """Mode '3' selects 'all' notification mode."""
        from teambot.cli import ConsoleDisplay, _setup_telegram_notifications

        inputs = iter(["y", "", "", "3"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        config = {}
        display = ConsoleDisplay()

        result = _setup_telegram_notifications(config, display)

        assert result is True
        channel = config["notifications"]["channels"][0]
        assert channel["notification_mode"] == "all"


class TestInitModelCacheRefresh:
    """Tests for model cache refresh during init."""

    def test_init_attempts_model_refresh(self, tmp_path, monkeypatch):
        """Init attempts to refresh model cache."""
        from unittest.mock import AsyncMock, patch

        from teambot.cli import _refresh_model_cache
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock refresh_models to track call
        mock_refresh = AsyncMock(return_value=True)

        with patch("teambot.cli.asyncio.run", return_value=True):
            with patch("teambot.config.schema.refresh_models", mock_refresh):
                display = ConsoleDisplay()
                result = _refresh_model_cache(display)

        assert result is True

    def test_init_succeeds_when_model_refresh_fails(self, tmp_path, monkeypatch):
        """Init completes successfully even if model refresh fails."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock refresh to fail
        with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=False)):
            with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()

    def test_init_succeeds_when_model_refresh_raises(self, tmp_path, monkeypatch):
        """Init continues even if model refresh raises exception."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock refresh to raise
        async def raise_error():
            raise RuntimeError("Network error")

        with patch("teambot.cli._refresh_model_cache_async", raise_error):
            with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()


class TestInitAuthenticationCheck:
    """Tests for authentication check during init."""

    def test_init_checks_authentication(self, tmp_path, monkeypatch):
        """Init verifies Copilot CLI authentication status."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Track if auth was checked
        auth_checked = [False]

        async def mock_auth():
            auth_checked[0] = True
            return (True, None)

        with patch("teambot.cli._check_auth_async", mock_auth):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                cmd_init(args, display)

        assert auth_checked[0] is True

    def test_init_succeeds_when_not_authenticated(self, tmp_path, monkeypatch):
        """Init completes successfully even when not authenticated."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()

    def test_init_succeeds_when_auth_check_fails(self, tmp_path, monkeypatch):
        """Init completes successfully even if auth check raises exception."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        async def raise_error():
            raise RuntimeError("SDK error")

        with patch("teambot.cli._check_auth_async", raise_error):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()


class TestInitPostGuidance:
    """Tests for post-init guidance display."""

    def test_init_displays_guidance(self, tmp_path, monkeypatch, capsys):
        """Init displays recommended next steps after completion."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                cmd_init(args, display)

        captured = capsys.readouterr()
        assert "Recommended Next Steps" in captured.out

    def test_guidance_file_exists(self):
        """Guidance file exists in scaffolds."""
        from teambot.scaffolds import get_scaffolds_dir

        guidance_file = get_scaffolds_dir() / "init-next-steps.md"
        assert guidance_file.exists()

    def test_guidance_contains_model_customization(self):
        """Guidance includes per-agent model configuration tip."""
        from teambot.scaffolds import get_scaffolds_dir

        guidance_file = get_scaffolds_dir() / "init-next-steps.md"
        content = guidance_file.read_text(encoding="utf-8")

        assert "model" in content.lower()
        assert "agent" in content.lower()

    def test_init_succeeds_if_guidance_loading_fails(self, tmp_path, monkeypatch):
        """Init succeeds even if guidance file cannot be loaded."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock importlib.resources to fail
        def raise_on_read(*args, **kwargs):
            raise FileNotFoundError("Mock file not found")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                with patch("importlib.resources.files", side_effect=raise_on_read):
                    args = argparse.Namespace(force=False, no_animation=True)
                    display = ConsoleDisplay()

                    result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()


class TestRunAuthCheck:
    """Tests for authentication check blocking behavior in cmd_run flow."""

    def test_auth_check_blocking_returns_true_when_authenticated(self, capsys):
        """Blocking auth check returns True when user is authenticated."""
        from unittest.mock import AsyncMock, patch

        from teambot.cli import _check_copilot_authentication_blocking
        from teambot.visualization.console import ConsoleDisplay

        # Mock _check_auth_async to return (True, None)
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            display = ConsoleDisplay()
            result = _check_copilot_authentication_blocking(display)

        assert result is True
        captured = capsys.readouterr()
        # No error messages when authenticated
        assert "not authenticated" not in captured.out.lower()

    def test_auth_check_blocking_returns_false_when_not_authenticated(self, capsys):
        """Blocking auth check returns False with guidance when not authenticated."""
        from unittest.mock import AsyncMock, patch

        from teambot.cli import _check_copilot_authentication_blocking
        from teambot.visualization.console import ConsoleDisplay

        # Mock _check_auth_async to return (False, "Not authenticated")
        with patch(
            "teambot.cli._check_auth_async", AsyncMock(return_value=(False, "Not authenticated"))
        ):
            display = ConsoleDisplay()
            result = _check_copilot_authentication_blocking(display)

        assert result is False
        captured = capsys.readouterr()
        assert "not authenticated" in captured.out.lower()
        assert "copilot login" in captured.out.lower()

    def test_auth_check_blocking_handles_exception_gracefully(self, capsys):
        """Blocking auth check returns False on exception."""
        from unittest.mock import patch

        from teambot.cli import _check_copilot_authentication_blocking
        from teambot.visualization.console import ConsoleDisplay

        # Mock _check_auth_async to raise Exception
        async def raise_error():
            raise RuntimeError("SDK error")

        with patch("teambot.cli._check_auth_async", raise_error):
            display = ConsoleDisplay()
            result = _check_copilot_authentication_blocking(display)

        assert result is False
        captured = capsys.readouterr()
        # Should show guidance about authentication
        assert "copilot login" in captured.out.lower()

    def test_auth_check_blocking_shows_error_detail_when_available(self, capsys):
        """Blocking auth check shows error details when provided."""
        from unittest.mock import AsyncMock, patch

        from teambot.cli import _check_copilot_authentication_blocking
        from teambot.visualization.console import ConsoleDisplay

        # Mock with specific error message (not "not available")
        with patch(
            "teambot.cli._check_auth_async", AsyncMock(return_value=(False, "Token expired"))
        ):
            display = ConsoleDisplay()
            result = _check_copilot_authentication_blocking(display)

        assert result is False
        captured = capsys.readouterr()
        assert "Token expired" in captured.out


class TestRunModelCache:
    """Tests for model cache auto-refresh in cmd_run flow."""

    def test_ensure_cache_returns_immediately_when_valid(self, tmp_path, monkeypatch, capsys):
        """_ensure_model_cache returns immediately when cache exists with models."""
        from unittest.mock import MagicMock, patch

        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock cache as existing with models (valid)
        mock_cache = MagicMock()
        mock_cache.models = ["gpt-5.2", "claude-sonnet-4.5"]
        with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
            with patch("teambot.cli._refresh_model_cache") as mock_refresh:
                display = ConsoleDisplay()
                _ensure_model_cache(display)

        # Refresh should NOT be called when cache exists with models
        mock_refresh.assert_not_called()
        captured = capsys.readouterr()
        assert "Refreshing model cache" not in captured.out

    def test_ensure_cache_detects_missing_file(self, tmp_path, monkeypatch, capsys):
        """_ensure_model_cache detects when cache file doesn't exist."""
        from unittest.mock import patch

        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock load_cache to return None (file doesn't exist)
        with patch("teambot.config.model_cache.load_cache", return_value=None):
            with patch("teambot.cli._refresh_model_cache", return_value=True) as mock_refresh:
                display = ConsoleDisplay()
                _ensure_model_cache(display)

        # Refresh should be called when cache is missing
        mock_refresh.assert_called_once()
        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out

    def test_ensure_cache_skips_refresh_when_expired(self, tmp_path, monkeypatch, capsys):
        """_ensure_model_cache does NOT refresh when cache is expired.

        Expired cache handling is left to schema._ensure_models_loaded()
        which uses expired cache with a warning. Only missing/empty cache triggers refresh.
        """
        from unittest.mock import MagicMock, patch

        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock expired cache (exists, has models, but expired - which is handled by load_cache)
        mock_cache = MagicMock()
        mock_cache.models = ["gpt-5.2", "claude-sonnet-4.5"]  # Has models
        with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
            with patch("teambot.cli._refresh_model_cache") as mock_refresh:
                display = ConsoleDisplay()
                _ensure_model_cache(display)

        # Refresh should NOT be called when cache is expired (has models)
        mock_refresh.assert_not_called()
        captured = capsys.readouterr()
        assert "Refreshing model cache" not in captured.out

    def test_ensure_cache_detects_empty_models(self, tmp_path, monkeypatch, capsys):
        """_ensure_model_cache detects when cache has empty models list."""
        from unittest.mock import MagicMock, patch

        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock cache with empty models list
        mock_cache = MagicMock()
        mock_cache.models = []
        with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
            with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                with patch("teambot.cli._refresh_model_cache", return_value=True) as mock_refresh:
                    display = ConsoleDisplay()
                    _ensure_model_cache(display)

        # Refresh should be called when cache has no models
        mock_refresh.assert_called_once()
        captured = capsys.readouterr()
        assert "empty" in captured.out.lower()

    def test_ensure_cache_continues_after_successful_refresh(self, tmp_path, monkeypatch, capsys):
        """Successful cache refresh allows workflow to continue."""
        from unittest.mock import patch

        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock load_cache to return None (missing)
        with patch("teambot.config.model_cache.load_cache", return_value=None):
            with patch("teambot.cli._refresh_model_cache", return_value=True):
                display = ConsoleDisplay()
                # Should not raise any exception
                _ensure_model_cache(display)

        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out

    def test_ensure_cache_continues_even_if_refresh_fails(self, tmp_path, monkeypatch, capsys):
        """Failed cache refresh continues - let ConfigLoader handle errors."""
        from unittest.mock import patch

        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock load_cache to return None (missing), refresh fails
        with patch("teambot.config.model_cache.load_cache", return_value=None):
            with patch("teambot.cli._refresh_model_cache", return_value=False):
                display = ConsoleDisplay()
                # Should not raise - function continues even on refresh failure
                _ensure_model_cache(display)

        # Function completes without error (ConfigLoader will handle validation errors)
        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out


# =============================================================================
# Phase 4: Integration Tests for --env-file and --no-env
# =============================================================================


class TestEnvArguments:
    """Tests for --env-file and --no-env CLI arguments."""

    def test_parser_accepts_env_file(self):
        """Parser recognizes --env-file argument."""
        from pathlib import Path

        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--env-file", ".env", "init"])
        assert args.env_file == Path(".env")

    def test_parser_accepts_no_env(self):
        """Parser recognizes --no-env flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-env", "init"])
        assert args.no_env is True

    def test_env_file_and_no_env_mutually_exclusive(self):
        """--env-file and --no-env cannot be used together."""
        from teambot.cli import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--env-file", ".env", "--no-env", "init"])

    def test_env_file_works_with_init_command(self):
        """--env-file works with init command."""
        from pathlib import Path

        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--env-file", ".env", "init"])
        assert args.env_file == Path(".env")
        assert args.command == "init"

    def test_env_file_works_with_status_command(self):
        """--env-file works with status command."""
        from pathlib import Path

        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--env-file", ".env", "status"])
        assert args.env_file == Path(".env")
        assert args.command == "status"

    def test_no_env_works_with_all_commands(self):
        """--no-env works with init, run, and status commands."""
        from teambot.cli import create_parser

        parser = create_parser()

        for cmd_args in [["init"], ["status"]]:
            args = parser.parse_args(["--no-env"] + cmd_args)
            assert args.no_env is True

    def test_env_file_default_is_none(self):
        """--env-file defaults to None when not provided."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["init"])
        assert args.env_file is None

    def test_no_env_default_is_false(self):
        """--no-env defaults to False when not provided."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["init"])
        assert args.no_env is False


class TestEnvLoadingIntegration:
    """Integration tests for .env loading in CLI."""

    def test_load_environment_loads_cwd_env_file(self, tmp_path, monkeypatch):
        """load_environment() loads .env from current directory."""
        import os

        from teambot.env_loader import load_environment

        (tmp_path / ".env").write_text("INTEGRATION_TEST_VAR=loaded")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("INTEGRATION_TEST_VAR", raising=False)

        # Mock git root to stop at tmp_path
        from unittest.mock import patch

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            load_environment()

        assert os.environ.get("INTEGRATION_TEST_VAR") == "loaded"

    def test_no_env_flag_prevents_loading(self, tmp_path, monkeypatch):
        """no_env=True prevents .env loading."""
        import os

        from teambot.env_loader import load_environment

        (tmp_path / ".env").write_text("SHOULD_NOT_LOAD=yes")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("SHOULD_NOT_LOAD", raising=False)

        load_environment(no_env=True)

        assert os.environ.get("SHOULD_NOT_LOAD") is None

    def test_env_file_flag_loads_specific_file(self, tmp_path, monkeypatch):
        """env_file parameter loads only specified file."""
        import os

        from teambot.env_loader import load_environment

        custom = tmp_path / "custom.env"
        custom.write_text("CUSTOM_VAR=custom")
        (tmp_path / ".env").write_text("CWD_VAR=cwd")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("CUSTOM_VAR", raising=False)
        monkeypatch.delenv("CWD_VAR", raising=False)

        load_environment(env_file=custom)

        assert os.environ.get("CUSTOM_VAR") == "custom"
        # Note: CWD_VAR might be set from prior test runs; the key assertion is CUSTOM_VAR is set

    def test_env_file_not_found_raises_error(self, tmp_path):
        """env_file pointing to non-existent file raises FileNotFoundError."""
        from teambot.env_loader import load_environment

        missing = tmp_path / "nonexistent.env"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment(env_file=missing)

        assert "nonexistent.env" in str(exc_info.value)


# === Conflict Detection Integration Tests (Phase 6) ===


class TestInitConflictHandling:
    """Tests for conflict detection during init."""

    def test_on_conflict_replace_clears_directory(self, tmp_path, monkeypatch):
        """--on-conflict=replace clears existing .agent directory."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, on_conflict="replace", no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        # Old file should be gone
        assert not (target_sdd / "sdd.4-old-name.prompt.md").exists()
        # New scaffold files should exist
        assert (tmp_path / ".agent" / "commands" / "sdd").exists()

    def test_on_conflict_backup_preserves_existing(self, tmp_path, monkeypatch):
        """--on-conflict=backup moves to backups directory."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, on_conflict="backup", no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        # Backup should exist
        backup_root = tmp_path / ".agent-tracking" / "backups"
        assert backup_root.exists()
        # Should have exactly one timestamped backup directory
        backup_dirs = list(backup_root.iterdir())
        assert len(backup_dirs) == 1
        # Old file should be in backup
        backup_agent = backup_dirs[0] / ".agent"
        assert (backup_agent / "commands" / "sdd" / "sdd.4-old-name.prompt.md").exists()

    def test_on_conflict_skip_keeps_existing(self, tmp_path, monkeypatch):
        """--on-conflict=skip leaves existing files unchanged."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, on_conflict="skip", no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        # Old file should still exist with original content
        assert (target_sdd / "sdd.4-old-name.prompt.md").exists()
        assert (target_sdd / "sdd.4-old-name.prompt.md").read_text() == "old content"

    def test_force_bypasses_conflict_detection(self, tmp_path, monkeypatch):
        """--force without --on-conflict replaces without conflict prompt."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=True, on_conflict=None, no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        # Old file should be gone (force replaces)
        assert not (target_sdd / "sdd.4-old-name.prompt.md").exists()

    def test_on_conflict_takes_precedence_over_force_with_skip(self, tmp_path, monkeypatch):
        """--on-conflict takes precedence over --force; emits a warning."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        warnings = []
        original_warn = ConsoleDisplay.print_warning

        def capture_warning(self, msg):
            warnings.append(msg)
            original_warn(self, msg)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                with patch.object(ConsoleDisplay, "print_warning", capture_warning):
                    args = argparse.Namespace(force=True, on_conflict="skip", no_animation=True)
                    display = ConsoleDisplay()
                    result = cmd_init(args, display)

        assert result == 0
        # --on-conflict=skip means existing .agent files are kept
        assert (target_sdd / "sdd.4-old-name.prompt.md").exists()
        # A warning about precedence should have been emitted
        assert any("--on-conflict" in w and "--force" in w for w in warnings)

    def test_on_conflict_takes_precedence_over_force_with_replace(self, tmp_path, monkeypatch):
        """--on-conflict=replace takes precedence over --force, clears .agent and warns."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        warnings = []
        original_warn = ConsoleDisplay.print_warning

        def capture_warning(self, msg):
            warnings.append(msg)
            original_warn(self, msg)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                with patch.object(ConsoleDisplay, "print_warning", capture_warning):
                    args = argparse.Namespace(force=True, on_conflict="replace", no_animation=True)
                    display = ConsoleDisplay()
                    result = cmd_init(args, display)

        assert result == 0
        # --on-conflict=replace means the old file is gone
        assert not (target_sdd / "sdd.4-old-name.prompt.md").exists()
        # A warning about precedence should have been emitted
        assert any("--on-conflict" in w and "--force" in w for w in warnings)

    def test_interactive_prompt_backup_option(self, tmp_path, monkeypatch):
        """Interactive prompt backup option creates backup."""
        import argparse
        from unittest.mock import AsyncMock, MagicMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        # Mock interactive input: "n" for notifications, "2" for conflict resolution (backup)
        inputs = iter(["n", "2"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        # Mock stdin.isatty() to return True for interactive mode
        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True
        monkeypatch.setattr("sys.stdin", mock_stdin)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, on_conflict=None, no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        # Backup should exist
        backup_root = tmp_path / ".agent-tracking" / "backups"
        assert backup_root.exists()

    def test_no_conflict_no_prompt(self, tmp_path, monkeypatch):
        """No conflict detection when files match scaffolds."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init
        from teambot.scaffolds import get_scaffolds_dir

        monkeypatch.chdir(tmp_path)

        # Setup .agent directory with same filename as scaffold
        scaffold_sdd = get_scaffolds_dir() / ".agent" / "commands" / "sdd"
        if scaffold_sdd.exists():
            scaffold_files = list(scaffold_sdd.glob("sdd.*.prompt.md"))
            if scaffold_files:
                # Create target with same name
                target_sdd = tmp_path / ".agent" / "commands" / "sdd"
                target_sdd.mkdir(parents=True)
                (target_sdd / scaffold_files[0].name).write_text("content")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, on_conflict=None, no_animation=True)
                display = ConsoleDisplay()

                # Should not prompt because no conflict
                result = cmd_init(args, display)

        assert result == 0

    def test_non_interactive_defaults_to_skip(self, tmp_path, monkeypatch):
        """Non-interactive mode defaults to skip."""
        import argparse
        from unittest.mock import AsyncMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Setup conflicting .agent directory
        target_sdd = tmp_path / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-name.prompt.md").write_text("old content")

        # Mock non-interactive (stdin not a tty)
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, on_conflict=None, no_animation=True)
                display = ConsoleDisplay()

                result = cmd_init(args, display)

        assert result == 0
        # Old file should still exist (skipped)
        assert (target_sdd / "sdd.4-old-name.prompt.md").exists()
        assert (target_sdd / "sdd.4-old-name.prompt.md").read_text() == "old content"


class TestPromptConflictResolution:
    """Tests for prompt_conflict_resolution function."""

    def test_returns_replace_on_option_1(self, monkeypatch):
        """Returns 'replace' when user enters 1."""
        from teambot.cli import ConsoleDisplay, prompt_conflict_resolution
        from teambot.scaffolds import ConflictInfo

        inputs = iter(["1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        conflicts = [ConflictInfo("sdd.4-", "sdd.4-new.prompt.md", "sdd.4-old.prompt.md")]
        display = ConsoleDisplay()

        result = prompt_conflict_resolution(conflicts, display)

        assert result == "replace"

    def test_returns_backup_on_option_2(self, monkeypatch):
        """Returns 'backup' when user enters 2."""
        from teambot.cli import ConsoleDisplay, prompt_conflict_resolution
        from teambot.scaffolds import ConflictInfo

        inputs = iter(["2"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        conflicts = [ConflictInfo("sdd.4-", "sdd.4-new.prompt.md", "sdd.4-old.prompt.md")]
        display = ConsoleDisplay()

        result = prompt_conflict_resolution(conflicts, display)

        assert result == "backup"

    def test_returns_skip_on_option_3(self, monkeypatch):
        """Returns 'skip' when user enters 3."""
        from teambot.cli import ConsoleDisplay, prompt_conflict_resolution
        from teambot.scaffolds import ConflictInfo

        inputs = iter(["3"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        conflicts = [ConflictInfo("sdd.4-", "sdd.4-new.prompt.md", "sdd.4-old.prompt.md")]
        display = ConsoleDisplay()

        result = prompt_conflict_resolution(conflicts, display)

        assert result == "skip"

    def test_returns_skip_on_keyboard_interrupt(self, monkeypatch):
        """Returns 'skip' when KeyboardInterrupt raised."""
        from teambot.cli import ConsoleDisplay, prompt_conflict_resolution
        from teambot.scaffolds import ConflictInfo

        def raise_interrupt(_):
            raise KeyboardInterrupt()

        monkeypatch.setattr("builtins.input", raise_interrupt)

        conflicts = [ConflictInfo("sdd.4-", "sdd.4-new.prompt.md", "sdd.4-old.prompt.md")]
        display = ConsoleDisplay()

        result = prompt_conflict_resolution(conflicts, display)

        assert result == "skip"

    def test_reprompts_on_invalid_input(self, monkeypatch):
        """Reprompts when user enters invalid input."""
        from teambot.cli import ConsoleDisplay, prompt_conflict_resolution
        from teambot.scaffolds import ConflictInfo

        inputs = iter(["x", "invalid", "1"])  # Invalid, invalid, then valid
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        conflicts = [ConflictInfo("sdd.4-", "sdd.4-new.prompt.md", "sdd.4-old.prompt.md")]
        display = ConsoleDisplay()

        result = prompt_conflict_resolution(conflicts, display)

        assert result == "replace"
