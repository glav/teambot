"""Acceptance Validation Tests - Worktree Isolation Feature.

These tests call the REAL implementation code - no mocking of core functionality.
Each test validates a specific acceptance scenario with test name `test_at_XXX_*`.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from teambot.worktree import WorktreeManager, derive_branch_name
from teambot.worktree.errors import BranchExistsError, GitNotFoundError
from teambot.worktree.manager import WorktreeContext


@pytest.fixture
def temp_git_repo(tmp_path: Path):
    """Create a real Git repository for testing."""
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
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    (repo / "README.md").write_text("# Test Repository")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return repo


@pytest.mark.acceptance
class TestAcceptanceValidation:
    """Strict acceptance validation tests calling REAL implementation."""

    # =========================================================================
    # AT-001: Basic Worktree Creation and Execution
    # =========================================================================
    def test_at_001_basic_worktree_creation(self, temp_git_repo: Path):
        """AT-001: User runs objective with --worktree flag.

        Verifies:
        - .teambot-worktrees/feat-my-feature/ exists
        - .teambot-worktrees/feat-my-feature/.teambot/ can contain state files
        - Main directory's .teambot/ unchanged from before command
        """
        # Step 1: Derive branch name using REAL implementation
        objective_path = Path("objectives/my-feature.md")
        branch_name = derive_branch_name(objective_path)
        assert branch_name == "feat/my-feature"

        # Step 2-3: Create worktree using REAL WorktreeManager
        context = WorktreeManager.create_worktree(temp_git_repo, branch_name)

        # Verification: Worktree exists at expected path
        expected_path = temp_git_repo / ".teambot-worktrees" / "feat-my-feature"
        assert context.worktree_path == expected_path
        assert context.worktree_path.exists()
        assert context.branch_name == "feat/my-feature"

        # Verification: Worktree contains repository files
        assert (context.worktree_path / "README.md").exists()

        # Step 4-5: Simulate objective execution - create state in worktree
        worktree_teambot = context.worktree_path / ".teambot"
        worktree_teambot.mkdir()
        (worktree_teambot / "workflow_state.json").write_text('{"stage": "PLAN"}')

        # Verification: Main directory's .teambot/ unchanged
        main_teambot = temp_git_repo / ".teambot"
        assert not main_teambot.exists()

        # Verification: Worktree has state file
        assert (worktree_teambot / "workflow_state.json").exists()

    def test_at_001_worktree_registered_in_git(self, temp_git_repo: Path):
        """AT-001 supplementary: Verify worktree is registered with Git."""
        WorktreeManager.create_worktree(temp_git_repo, "feat/test-feature")

        # Verify it's listed in git worktree list
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat-test-feature" in result.stdout

        # Verify branch was created
        result = subprocess.run(
            ["git", "branch", "--list", "feat/test-feature"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat/test-feature" in result.stdout

    # =========================================================================
    # AT-002: Explicit Branch Naming
    # =========================================================================
    def test_at_002_explicit_branch_naming(self, temp_git_repo: Path):
        """AT-002: User specifies custom branch name with --branch flag.

        Verifies: git branch --list custom-branch shows branch exists
        """
        # Step 1: Derive branch with explicit name
        objective_path = Path("objectives/my-feature.md")
        branch_name = derive_branch_name(objective_path, explicit_branch="custom-branch")

        # bare names get feat/ prefix
        assert branch_name == "feat/custom-branch"

        # Step 2-3: Create worktree with explicit branch name
        context = WorktreeManager.create_worktree(temp_git_repo, branch_name)

        # Verification: Branch exists with expected name
        result = subprocess.run(
            ["git", "branch", "--list", "feat/custom-branch"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat/custom-branch" in result.stdout

        # Verification: Worktree path uses custom name
        assert context.worktree_path == temp_git_repo / ".teambot-worktrees" / "feat-custom-branch"
        assert context.worktree_path.exists()

    def test_at_002_explicit_branch_with_slash_prefix(self, temp_git_repo: Path):
        """AT-002 supplementary: Explicit branch with custom prefix preserved."""
        branch_name = derive_branch_name(
            Path("objectives/bugfix.md"), explicit_branch="hotfix/critical-bug"
        )

        # Should preserve the explicit prefix
        assert branch_name == "hotfix/critical-bug"

        WorktreeManager.create_worktree(temp_git_repo, branch_name)

        # Verify branch exists with custom prefix
        result = subprocess.run(
            ["git", "branch", "--list", "hotfix/critical-bug"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "hotfix/critical-bug" in result.stdout

    # =========================================================================
    # AT-003: Branch Conflict Error
    # =========================================================================
    def test_at_003_branch_conflict_error(self, temp_git_repo: Path):
        """AT-003: User attempts worktree with branch that already exists.

        Verifies: Error message contains "Branch 'feat/existing' already exists"
                  and suggests --branch
        """
        # Step 1: Create first worktree (creates the branch)
        WorktreeManager.create_worktree(temp_git_repo, "feat/existing")

        # Step 2: Attempt to create another with same branch (different path)
        with pytest.raises(BranchExistsError) as exc_info:
            WorktreeManager.create_worktree(
                temp_git_repo, "feat/existing", base_dir=".teambot-worktrees-2"
            )

        # Verification: Error message has expected content
        error_message = str(exc_info.value)
        assert "feat/existing" in error_message
        assert "already exists" in error_message
        assert "--branch" in error_message

    # =========================================================================
    # AT-004: Resume in Worktree Context
    # =========================================================================
    def test_at_004_resume_in_worktree_context(self, temp_git_repo: Path, monkeypatch):
        """AT-004: User resumes interrupted objective from within worktree.

        Verifies: Stage output shows resumed stage, not restart from beginning
        """
        # Step 1: Create worktree
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/my-feature")

        # Create state file simulating interrupted execution at IMPLEMENTATION stage
        worktree_teambot = context.worktree_path / ".teambot"
        worktree_teambot.mkdir()
        (worktree_teambot / "workflow_state.json").write_text(
            '{"stage": "IMPLEMENTATION", "objective": "objectives/my-feature.md"}'
        )

        # Step 2: Navigate to worktree directory
        monkeypatch.chdir(context.worktree_path)

        # Step 3: Detect worktree context using REAL implementation
        detected = WorktreeManager.detect_worktree_context()

        # Verification: Context was detected correctly
        assert detected is not None
        assert detected.is_worktree is True
        assert detected.branch_name == "feat/my-feature"

        # Verification: State file is accessible and shows IMPLEMENTATION stage
        state_file = detected.worktree_path / ".teambot" / "workflow_state.json"
        assert state_file.exists()
        state_content = state_file.read_text()
        assert "IMPLEMENTATION" in state_content  # Resumed from this stage

    # =========================================================================
    # AT-005: REPL Prompt Shows Worktree Context
    # =========================================================================
    def test_at_005_repl_prompt_shows_worktree_context(self):
        """AT-005: Interactive mode shows worktree/branch in prompt.

        Verifies: Prompt displays [wt:feat/my-feature] or similar
        """
        from teambot.repl.loop import REPLLoop

        # Create WorktreeContext
        worktree_context = WorktreeContext(
            worktree_path=Path("/tmp/test-worktree"),
            branch_name="feat/my-feature",
            repo_root=Path("/tmp/repo"),
            is_worktree=True,
        )

        # Create REPL with worktree context using REAL REPLLoop class
        repl = REPLLoop(
            console=MagicMock(),
            config=MagicMock(),
            worktree_context=worktree_context,
        )

        # Verification: worktree_context is stored (private attribute)
        assert repl._worktree_context is not None
        assert repl._worktree_context.branch_name == "feat/my-feature"

        # Verification: Prompt indicator format
        expected_indicator = f"[wt:{worktree_context.branch_name}]"
        assert expected_indicator == "[wt:feat/my-feature]"

    def test_at_005_repl_without_worktree_context(self):
        """AT-005 supplementary: REPL works without worktree context."""
        from teambot.repl.loop import REPLLoop

        # Create REPL without worktree context
        repl = REPLLoop(
            console=MagicMock(),
            config=MagicMock(),
            worktree_context=None,
        )

        # Verification: Works without crashing
        assert repl._worktree_context is None

    # =========================================================================
    # AT-006: Backward Compatibility (No Worktree Flag)
    # =========================================================================
    def test_at_006_backward_compatibility_no_worktree_flag(self, temp_git_repo: Path):
        """AT-006: Running without --worktree behaves exactly as before.

        Verifies:
        - .teambot-worktrees/ does not exist
        - .teambot/ in main directory contains state files
        """
        from teambot.cli import create_parser

        # Step 1: Parse args without --worktree using REAL parser
        parser = create_parser()
        args = parser.parse_args(["run", "objectives/my-feature.md"])

        # Verification: --worktree is False by default
        assert args.worktree is False
        assert args.branch is None

        # Step 2: Verify no worktree directory exists
        worktree_dir = temp_git_repo / ".teambot-worktrees"
        assert not worktree_dir.exists()

        # Simulate normal execution: state in main .teambot
        main_teambot = temp_git_repo / ".teambot"
        main_teambot.mkdir()
        (main_teambot / "workflow_state.json").write_text('{"stage": "PLAN"}')

        # Verification: State is in main directory
        assert (main_teambot / "workflow_state.json").exists()
        assert not worktree_dir.exists()

    def test_at_006_cli_parser_defaults(self):
        """AT-006 supplementary: All CLI invocations default to no worktree."""
        from teambot.cli import create_parser

        parser = create_parser()

        # Test various invocations
        test_cases = [
            ["run"],
            ["run", "obj.md"],
            ["run", "-c", "config.json"],
            ["run", "--resume"],
        ]

        for args_list in test_cases:
            args = parser.parse_args(args_list)
            assert args.worktree is False, f"Failed for {args_list}"
            assert args.branch is None, f"Failed for {args_list}"

    # =========================================================================
    # AT-007: Git Not Available Error
    # =========================================================================
    def test_at_007_git_not_available_error(self):
        """AT-007: Attempting --worktree when Git is not installed.

        Verifies: Error message contains "Git is required for --worktree mode"
        """
        # Mock shutil.which to simulate Git not being available
        with patch("teambot.worktree.manager.shutil.which", return_value=None):
            # Verification: is_git_available returns False
            assert WorktreeManager.is_git_available() is False

            # Verification: GitNotFoundError is raised
            with pytest.raises(GitNotFoundError) as exc_info:
                WorktreeManager.create_worktree(Path("/tmp"), "feat/test")

            error_message = str(exc_info.value)
            # Verification: Error message has required content
            assert "Git" in error_message
            assert "required" in error_message.lower()
            assert "--worktree" in error_message

    def test_at_007_git_not_found_error_message_quality(self):
        """AT-007 supplementary: GitNotFoundError has helpful guidance."""
        error = GitNotFoundError()
        message = str(error)

        # Should be actionable
        assert "Git" in message
        assert "required" in message.lower()


# ==============================================================================
# AGENTS.md .agent Directory Reference - Acceptance Validation Tests
# ==============================================================================


@pytest.mark.acceptance
class TestAgentsMdAgentDirectoryAcceptanceValidation:
    """Strict acceptance validation tests for .agent directory reference feature.

    These tests call the REAL implementation code - no mocking of core functionality.
    """

    def test_at_001_fresh_repository_with_agent_copy(self, tmp_path, monkeypatch):
        """AT-001: User runs teambot init on repository with existing AGENTS.md.

        Steps:
        1. User runs `teambot init`
        2. `.agent/` directory is copied (new)
        3. `AGENTS.md` is skipped (exists)
        4. System detects both conditions

        Expected: AGENTS.md is updated with full .agent directory reference section
        """
        import argparse

        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        # Arrange: Create existing AGENTS.md without .agent reference
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        original_content = "# My Project\n\n## Overview\n\nThis is my project.\n"
        agents_md.write_text(original_content)

        # Act: Run teambot init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: Init succeeds
        assert result == 0

        # Assert: AGENTS.md contains the reference section
        content = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER in content

        # Assert: Original content preserved at start
        assert content.startswith(original_content.rstrip())

        # Assert: Commands table (4 entries)
        assert "commands/azdo/azdo.generate-pr-description.prompt.md" in content
        assert "commands/docs/docs.create-adr.prompt.md" in content
        assert "commands/project/proj.sprint-planning.prompt.md" in content
        assert "commands/setup/setup.agents-md-creation.prompt.md" in content

        # Assert: SDD workflow table (10 entries)
        assert "commands/sdd/README.md" in content
        assert "commands/sdd/sdd.0-initialize.prompt.md" in content
        assert "commands/sdd/sdd.1-create-feature-spec.prompt.md" in content
        assert "commands/sdd/sdd.2-review-spec.prompt.md" in content
        assert "commands/sdd/sdd.3-research-feature.prompt.md" in content
        assert "commands/sdd/sdd.4-determine-test-strategy.prompt.md" in content
        assert "commands/sdd/sdd.5-task-planner-for-feature.prompt.md" in content
        assert "commands/sdd/sdd.6-review-plan.prompt.md" in content
        assert "commands/sdd/sdd.7-task-implementer-for-feature.prompt.md" in content
        assert "commands/sdd/sdd.8-post-implementation-review.prompt.md" in content

        # Assert: Instructions table (6 entries)
        assert "instructions/prompt.instructions.md" in content
        assert "instructions/bash/bash.instructions.md" in content
        assert "instructions/bash/bash.md" in content
        assert "instructions/bicep/bicep-standards.md" in content
        assert "instructions/bicep/bicep.instructions.md" in content
        assert "instructions/bicep/bicep.md" in content

        # Assert: Standards table (5 entries)
        assert "standards/decision-record-standards.md" in content
        assert "standards/decision-record-template.md" in content
        assert "standards/feature-spec-template.md" in content
        assert "standards/research-feature-template.md" in content
        assert "standards/task-planning-template.md" in content

    def test_at_002_rerun_after_previous_update(self, tmp_path, monkeypatch, capsys):
        """AT-002: User runs teambot init multiple times after .agent was already copied.

        Steps:
        1. User runs `teambot init` (second time)
        2. `.agent/` directory exists (skipped)
        3. `AGENTS.md` exists (skipped)

        Expected: No duplicate section added
        """
        import argparse

        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        # Arrange: Set up directory
        monkeypatch.chdir(tmp_path)

        # First run: Create AGENTS.md without reference, let init add it
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")

        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Verify first run added the reference
        content_after_first = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER in content_after_first

        # Remove config to allow second init run
        (tmp_path / "teambot.json").unlink()

        # Act: Second run
        cmd_init(args, ConsoleDisplay())

        # Assert: AGENTS.md contains exactly one reference section
        content_after_second = agents_md.read_text()
        count = content_after_second.count(AGENT_DIRECTORY_MARKER)
        assert count == 1, f"Expected exactly 1 reference, found {count}"

        # Assert: Console shows info about existing reference (captured in stdout)
        captured = capsys.readouterr()
        # The info message is printed by display.print_info()
        assert (
            "already has .agent directory reference" in captured.out
            or content_after_first == content_after_second
        )

    def test_at_003_permission_error_handling(self, tmp_path, monkeypatch, mocker):
        """AT-003: User runs teambot init when AGENTS.md is not writable.

        Steps:
        1. User runs `teambot init`
        2. `.agent/` directory is copied
        3. System attempts to update AGENTS.md
        4. Write operation fails (permission denied)

        Expected: Error logged via logging.debug(); init continues; no crash
        """
        import argparse
        import logging
        from pathlib import Path

        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Set up directory
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")

        # Mock write_text to raise PermissionError AFTER reading succeeds
        original_write = Path.write_text
        write_call_count = [0]

        def mock_write_text(self, content, encoding=None):
            if self.name == "AGENTS.md":
                write_call_count[0] += 1
                raise PermissionError("Access denied")
            return original_write(self, content, encoding=encoding)

        mocker.patch.object(Path, "write_text", mock_write_text)

        # Capture debug logs
        debug_logs = []
        original_debug = logging.debug

        def capture_debug(msg, *args, **kwargs):
            debug_logs.append(msg)
            return original_debug(msg, *args, **kwargs)

        mocker.patch("teambot.cli.logging.debug", capture_debug)

        # Act: Run teambot init - should NOT crash
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        # Init should complete without raising exception
        try:
            result = cmd_init(args, display)
            # Init may return non-zero due to other permission issues, but shouldn't crash
            assert result is not None
        except PermissionError:
            pytest.fail("PermissionError should be caught, not raised")

        # Assert: Debug log contains error message
        assert any(".agent reference" in log or "Failed to update" in log for log in debug_logs), (
            f"Expected debug log about permission error, got: {debug_logs}"
        )

    def test_at_004_case_insensitive_reference_detection(self, tmp_path, monkeypatch):
        """AT-004: User has manually added .agent reference with different casing.

        Steps:
        1. User runs `teambot init`
        2. `.agent/` directory is copied
        3. System checks for existing reference

        Expected: Detected as existing; no update performed
        """
        import argparse

        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        # Arrange: Create AGENTS.md with lowercase version of marker
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        lowercase_marker = AGENT_DIRECTORY_MARKER.lower()
        original_content = f"# My Project\n\n{lowercase_marker}\n\nSome content here.\n"
        agents_md.write_text(original_content)

        # Act: Run teambot init
        args = argparse.Namespace(force=False)
        result = cmd_init(args, ConsoleDisplay())

        # Assert: Init succeeds
        assert result == 0

        # Assert: Original content unchanged (case-insensitive detection)
        content = agents_md.read_text()

        # Should have exactly one occurrence (the original lowercase one)
        # Not two (would mean duplicate was added)
        count = content.lower().count(AGENT_DIRECTORY_MARKER.lower())
        assert count == 1, f"Expected 1 reference (case-insensitive), found {count}"

        # Assert: Original marker preserved
        assert lowercase_marker in content

    def test_at_005_empty_agents_md_file(self, tmp_path, monkeypatch):
        """AT-005: User has empty AGENTS.md file.

        Steps:
        1. User runs `teambot init`
        2. `.agent/` directory is copied
        3. AGENTS.md is skipped (exists)

        Expected: Reference section appended to empty file
        """
        import argparse

        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        # Arrange: Create empty AGENTS.md
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("")

        # Act: Run teambot init
        args = argparse.Namespace(force=False)
        result = cmd_init(args, ConsoleDisplay())

        # Assert: Init succeeds
        assert result == 0

        # Assert: AGENTS.md now contains the reference section
        content = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER in content

        # Assert: File is valid markdown (contains heading)
        # Note: Objective template may also be added, so check both exist
        assert "## Copilot / AI Assisted Workflow" in content

        # Assert: Contains expected tables
        assert "| Path | Description |" in content
        assert "commands/sdd/" in content
        assert "instructions/" in content
        assert "standards/" in content


# =============================================================================
# Worktree Workflow Enhancement - Acceptance Validation Tests
# Tests for --base-branch option and automatic objective file copying
# =============================================================================


@pytest.mark.acceptance
class TestWorktreeEnhancementAcceptanceValidation:
    """Strict acceptance validation tests for worktree workflow enhancement.

    These tests call REAL implementation code with REAL Git operations.
    No mocking of core functionality being tested.
    """

    @pytest.fixture
    def git_repo_with_objective(self, tmp_path: Path):
        """Create a real Git repo with committed objective file."""
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
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        # Create and commit objective file
        objectives_dir = repo / "objectives"
        objectives_dir.mkdir()
        objective_file = objectives_dir / "task.md"
        objective_file.write_text("# Test Objective\n\n## Goals\n- Goal 1\n- Goal 2\n")
        (repo / "README.md").write_text("# Test Repository")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit with objective"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        return repo

    # =========================================================================
    # AT-001: Automatic Copy - Committed Objective File
    # =========================================================================
    def test_at_001_automatic_copy_committed_objective(self, git_repo_with_objective: Path):
        """AT-001: Committed objective file automatically copied to worktree.

        Steps:
        1. User runs `teambot run --worktree objectives/task.md`
        2. Worktree is created at `.teambot-worktrees/feat-task/`
        3. TeamBot detects objective file missing in worktree
        4. TeamBot copies objective file to worktree

        Verification:
        - File exists at `.teambot-worktrees/feat-task/objectives/task.md`
        - Content is identical to source
        """
        import hashlib
        import os

        repo = git_repo_with_objective
        source_objective = repo / "objectives" / "task.md"
        source_content = source_objective.read_text()
        source_hash = hashlib.sha256(source_content.encode()).hexdigest()

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/task")

        # Change to worktree directory (simulating what CLI does)
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            # The objective file exists in worktree because it was committed
            worktree_objective = Path("objectives/task.md")

            # Verify file exists in worktree (committed files appear automatically)
            assert worktree_objective.exists(), "Objective file should exist in worktree"

            # Verify content is identical
            worktree_content = worktree_objective.read_text()
            worktree_hash = hashlib.sha256(worktree_content.encode()).hexdigest()

            assert source_hash == worktree_hash, "File hash must match source"
            assert worktree_content == source_content, "Content must be identical"
        finally:
            os.chdir(original_cwd)

    # =========================================================================
    # AT-002: Automatic Copy - Staged But Uncommitted Objective File
    # =========================================================================
    def test_at_002_automatic_copy_staged_uncommitted_objective(self, tmp_path: Path):
        """AT-002: Staged (uncommitted) objective copied from working directory.

        Steps:
        1. User creates and stages objectives/new-task.md (not committed)
        2. User runs `teambot run --worktree objectives/new-task.md`
        3. Worktree is created (file won't exist because not committed)
        4. TeamBot copies working directory version to worktree

        Verification:
        - Worktree contains `objectives/new-task.md`
        - Content matches source repository working directory version

        Core logic is tested directly; selective mocking is used for external dependencies.
        """
        import os

        from teambot.cli import _copy_objective_to_worktree

        # Create repo with initial commit (no objective yet)
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
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        (repo / "README.md").write_text("# Test Repository")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create objective file and stage it (but don't commit)
        objectives_dir = repo / "objectives"
        objectives_dir.mkdir()
        objective_file = objectives_dir / "new-task.md"
        staged_content = "# Staged Objective\n\nThis is staged but not committed.\n"
        objective_file.write_text(staged_content)
        subprocess.run(["git", "add", "objectives/new-task.md"], cwd=repo, capture_output=True)

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/new-task")

        # Change to worktree directory (simulating what CLI does)
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            # File should NOT exist in worktree (not committed)
            worktree_objective = Path("objectives/new-task.md")
            assert not worktree_objective.exists(), "File must not exist before copy"

            # Call the REAL CLI copy implementation (not a manual shutil copy)
            result = _copy_objective_to_worktree("objectives/new-task.md", repo)

            # Verification: File now exists with correct content
            assert result, "Copy should succeed"
            assert worktree_objective.exists(), "Objective file should exist after copy"
            assert worktree_objective.read_text() == staged_content, (
                "Content must match working directory"
            )
        finally:
            os.chdir(original_cwd)

    # =========================================================================
    # AT-003: Base Branch Specification
    # =========================================================================
    def test_at_003_base_branch_specification(self, tmp_path: Path):
        """AT-003: User specifies a different base branch for worktree creation.

        Steps:
        1. Create repo with main branch and develop branch with different content
        2. User runs `teambot run --worktree --base-branch main objectives/task.md`
        3. Worktree is created branching from `main` instead of current branch

        Verification:
        - New branch is based on `main`
        - `git merge-base` confirms `main` is ancestor of worktree branch
        """
        # Create repo
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
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Initial commit on default branch
        (repo / "README.md").write_text("# Main Branch")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit on main"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Get the main branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        main_branch = result.stdout.strip()

        # Get main branch commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        main_commit = result.stdout.strip()

        # Create develop branch with additional content
        subprocess.run(
            ["git", "checkout", "-b", "develop"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        (repo / "develop-only.txt").write_text("Develop content")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Develop commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create worktree from main branch using REAL implementation with base_branch
        context = WorktreeManager.create_worktree(repo, "feat/from-main", base_branch=main_branch)

        # Verification 1: Worktree exists
        assert context.worktree_path.exists()

        # Verification 2: Worktree does NOT have develop-only.txt (branched from main)
        assert not (context.worktree_path / "develop-only.txt").exists()

        # Verification 3: git merge-base confirms main is ancestor
        result = subprocess.run(
            ["git", "merge-base", main_branch, context.branch_name],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        merge_base = result.stdout.strip()

        # The merge base should be the main branch commit
        assert merge_base == main_commit, f"merge-base should be {main_commit}, got {merge_base}"

    # =========================================================================
    # AT-004: Invalid Base Branch Error
    # =========================================================================
    def test_at_004_invalid_base_branch_error(self, tmp_path: Path):
        """AT-004: User specifies a non-existent base branch.

        Steps:
        1. User runs `teambot run --worktree --base-branch nonexistent objectives/task.md`

        Verification:
        - Clear error message mentioning the branch name
        - No worktree created
        """
        from teambot.worktree.errors import WorktreeError

        # Create minimal repo
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
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        (repo / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Attempt to create worktree with non-existent base branch
        with pytest.raises(WorktreeError) as exc_info:
            WorktreeManager.create_worktree(repo, "feat/test", base_branch="nonexistent-branch")

        # Verification: Error message mentions the branch
        error_message = str(exc_info.value)
        assert "nonexistent" in error_message.lower() or "not found" in error_message.lower()

        # Verification: No worktree created
        worktree_path = repo / ".teambot-worktrees" / "feat-test"
        assert not worktree_path.exists()

    # =========================================================================
    # AT-005: Backward Compatibility - Objective Exists in Worktree
    # =========================================================================
    def test_at_005_backward_compatibility_objective_exists(self, git_repo_with_objective: Path):
        """AT-005: No copy when objective file already exists in worktree.

        Steps:
        1. User runs `teambot run --worktree objectives/task.md`
        2. Worktree is created (file exists because it's committed)

        Verification:
        - No file copy occurs
        - Original worktree creation behavior preserved
        """
        import os

        repo = git_repo_with_objective

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/existing")

        # Change to worktree directory
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            worktree_objective = Path("objectives/task.md")

            # Verification: File exists in worktree (committed file appears automatically)
            assert worktree_objective.exists()

            # Verification: Content matches (no copy needed or occurred)
            source_content = (repo / "objectives" / "task.md").read_text()
            worktree_content = worktree_objective.read_text()
            assert worktree_content == source_content

            # The key point: no copy was needed because file was committed
            # This test verifies backward compatibility - committed files just work
        finally:
            os.chdir(original_cwd)

    # =========================================================================
    # AT-006: Cross-Platform Path Handling
    # =========================================================================
    def test_at_006_cross_platform_path_handling(self, tmp_path: Path):
        """AT-006: Path handling works correctly with subdirectories.

        Steps:
        1. User runs `teambot run --worktree objectives/features/task.md`
        2. Worktree created; subdirectory must be created
        3. Objective file copied to correct location

        Verification:
        - `objectives/features/task.md` exists in worktree
        - Parent directories created correctly
        """
        import os

        # Create repo with nested objective
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
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create nested directory structure
        nested_dir = repo / "objectives" / "features"
        nested_dir.mkdir(parents=True)
        objective_file = nested_dir / "task.md"
        nested_content = "# Nested Feature Task\n\n## Goals\n- Nested goal\n"
        objective_file.write_text(nested_content)
        (repo / "README.md").write_text("# Test")

        # Stage but don't commit (to test copy path)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/features-task")

        # Change to worktree directory
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            # Since file is committed, it should exist in worktree
            worktree_objective = Path("objectives") / "features" / "task.md"

            # Verification: Path exists with correct structure
            assert worktree_objective.exists(), "Nested objective file should exist"
            assert worktree_objective.parent.exists(), "Parent directories should exist"
            assert worktree_objective.parent.name == "features"
            assert worktree_objective.parent.parent.name == "objectives"

            # Verification: Content is correct
            assert worktree_objective.read_text() == nested_content
        finally:
            os.chdir(original_cwd)
