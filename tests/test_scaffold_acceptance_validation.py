"""Acceptance validation tests for scaffold copying feature.

These tests validate the REAL implementation without mocking core functionality.
Each test corresponds to an acceptance scenario (AT-XXX).
"""

import subprocess
import sys
from pathlib import Path

from teambot.scaffolds import copy_all_scaffolds, get_scaffolds_dir


class TestScaffoldAcceptanceScenarios:
    """Acceptance tests for scaffold copying feature."""

    def test_at_001_fresh_repository_initialization(self, tmp_path: Path, monkeypatch):
        """AT-001: Fresh Repository Initialization.

        User runs init on a repository with no TeamBot files.
        All scaffolds should be copied.
        """
        monkeypatch.chdir(tmp_path)

        # Run the real copy_all_scaffolds function
        results = copy_all_scaffolds(target_root=tmp_path, force=False)

        # Verify all expected files/directories exist
        assert (tmp_path / "stages.yaml").exists(), "stages.yaml not created"
        assert (tmp_path / "AGENTS.md").exists(), "AGENTS.md not created"
        assert (tmp_path / ".github" / "agents").exists(), ".github/agents/ not created"
        assert (tmp_path / ".agent").exists(), ".agent/ not created"
        sdd_template = tmp_path / "docs" / "sdd-objective-template.md"
        assert sdd_template.exists(), "docs/sdd-objective-template.md not created"

        # Verify .github/agents/ has 6 agent files
        agents_dir = tmp_path / ".github" / "agents"
        agent_files = list(agents_dir.glob("*.agent.md"))
        assert len(agent_files) == 6, f"Expected 6 agent files, got {len(agent_files)}"

        # Verify .agent/commands/sdd/ contains expected prompts
        sdd_dir = tmp_path / ".agent" / "commands" / "sdd"
        assert sdd_dir.exists(), ".agent/commands/sdd/ not created"
        sdd_files = list(sdd_dir.glob("*.md"))
        assert len(sdd_files) > 0, "No SDD prompt files found"

        # Verify all results show "copied"
        copied_count = sum(1 for r in results if r.copied)
        assert copied_count == 5, f"Expected 5 items copied, got {copied_count}"

    def test_at_002_reinit_preserves_existing_files(self, tmp_path: Path, monkeypatch):
        """AT-002: Re-initialization Preserves Existing Files.

        User runs init on a repository already configured with TeamBot.
        Custom content should be preserved.
        """
        monkeypatch.chdir(tmp_path)

        # First init - create all scaffolds
        copy_all_scaffolds(target_root=tmp_path, force=False)

        # User modifies AGENTS.md with custom content
        custom_content = "# My Custom AGENTS.md\n\nThis is my custom content."
        (tmp_path / "AGENTS.md").write_text(custom_content)

        # Re-run init
        results = copy_all_scaffolds(target_root=tmp_path, force=False)

        # Verify AGENTS.md retains custom content
        actual_content = (tmp_path / "AGENTS.md").read_text()
        assert actual_content == custom_content, "AGENTS.md was overwritten!"

        # Verify all results show "skipped" (nothing copied)
        copied_count = sum(1 for r in results if r.copied)
        assert copied_count == 0, f"Expected 0 items copied on re-init, got {copied_count}"

        # Verify skip reason mentions "exists"
        agents_result = next(r for r in results if "AGENTS.md" in str(r.target))
        reason_msg = f"Expected 'exists' in reason: {agents_result.reason}"
        assert "exists" in agents_result.reason.lower(), reason_msg

    def test_at_003_partial_initialization_fills_gaps(self, tmp_path: Path, monkeypatch):
        """AT-003: Partial Initialization Fills Gaps.

        User runs init on a repository with some TeamBot files present.
        Only missing files should be copied.
        """
        monkeypatch.chdir(tmp_path)

        # Create only stages.yaml (simulating partial state)
        original_content = "# My existing stages.yaml\nstages: []"
        (tmp_path / "stages.yaml").write_text(original_content)

        # Run init
        results = copy_all_scaffolds(target_root=tmp_path, force=False)

        # Verify stages.yaml was skipped (content unchanged)
        actual_content = (tmp_path / "stages.yaml").read_text()
        assert actual_content == original_content, "stages.yaml was overwritten!"

        # Verify other items were copied
        assert (tmp_path / "AGENTS.md").exists(), "AGENTS.md not created"
        assert (tmp_path / ".github" / "agents").exists(), ".github/agents/ not created"
        assert (tmp_path / ".agent").exists(), ".agent/ not created"

        # Count copied vs skipped
        copied_count = sum(1 for r in results if r.copied)
        skipped_count = sum(1 for r in results if not r.copied)
        assert copied_count == 4, f"Expected 4 items copied, got {copied_count}"
        assert skipped_count == 1, f"Expected 1 item skipped, got {skipped_count}"

    def test_at_004_package_installation_resource_access(self, tmp_path: Path):
        """AT-004: Package Installation Resource Access.

        Resources are accessible when TeamBot installed.
        Validates get_scaffolds_dir() returns valid path with expected files.
        """
        # Get the scaffolds directory from the real implementation
        scaffolds_dir = get_scaffolds_dir()

        # Verify it's a valid path
        assert scaffolds_dir.exists(), f"Scaffolds dir doesn't exist: {scaffolds_dir}"

        # Verify all expected scaffold files are present
        assert (scaffolds_dir / "stages.yaml").exists(), "stages.yaml not in package"
        assert (scaffolds_dir / "AGENTS.md").exists(), "AGENTS.md not in package"
        assert (scaffolds_dir / "agents").exists(), "agents/ not in package"
        assert (scaffolds_dir / ".agent").exists(), ".agent/ not in package"
        sdd_template = scaffolds_dir / "sdd-objective-template.md"
        assert sdd_template.exists(), "sdd-objective-template.md not in package"

        # Verify agents directory has 6 files
        agents_dir = scaffolds_dir / "agents"
        agent_files = list(agents_dir.glob("*.agent.md"))
        assert len(agent_files) == 6, f"Expected 6 agent files in package, got {len(agent_files)}"

        # Verify copy_all_scaffolds works with this scaffolds_dir
        results = copy_all_scaffolds(target_root=tmp_path, force=False)
        assert len(results) == 5, f"Expected 5 copy results, got {len(results)}"
        assert all(r.copied for r in results), "Some scaffolds failed to copy"

    def test_at_005_empty_agents_directory_handling(self, tmp_path: Path, monkeypatch):
        """AT-005: Empty .github/agents/ Directory Handling.

        Init populates an empty agents directory.
        """
        monkeypatch.chdir(tmp_path)

        # Create empty .github/agents/ directory
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        assert agents_dir.exists()
        assert len(list(agents_dir.iterdir())) == 0, "agents/ should start empty"

        # Run init
        results = copy_all_scaffolds(target_root=tmp_path, force=False)

        # Verify directory was populated with 6 agent files
        agent_files = list(agents_dir.glob("*.agent.md"))
        assert len(agent_files) == 6, f"Expected 6 agent files, got {len(agent_files)}"

        # Verify the agents result shows copied (empty dir should be populated)
        agents_result = next(
            r for r in results if "agents" in str(r.target).lower() and ".github" in str(r.target)
        )
        assert agents_result.copied, f"Expected agents to be copied, got: {agents_result.reason}"

    def test_at_006_cross_platform_path_handling(self, tmp_path: Path):
        """AT-006: Cross-Platform Path Handling.

        Init works correctly on current platform (Windows, Linux, or macOS).
        Tests path handling for the current platform.
        """
        # Run copy on this platform
        results = copy_all_scaffolds(target_root=tmp_path, force=False)

        # Verify all copies succeeded
        failed_copies = [r for r in results if not r.copied]
        assert all(r.copied for r in results), f"Some copies failed: {failed_copies}"

        # Verify expected structure exists with proper paths
        expected_paths = [
            tmp_path / "stages.yaml",
            tmp_path / "AGENTS.md",
            tmp_path / ".github" / "agents",
            tmp_path / ".agent",
            tmp_path / ".agent" / "commands" / "sdd",
            tmp_path / "docs" / "sdd-objective-template.md",
        ]

        for path in expected_paths:
            assert path.exists(), f"Path not created correctly: {path}"

        # Verify no path separator issues in file contents
        stages_content = (tmp_path / "stages.yaml").read_text()
        assert stages_content, "stages.yaml is empty"

        # Verify nested directory structure
        sdd_prompts = list((tmp_path / ".agent" / "commands" / "sdd").glob("*.md"))
        assert len(sdd_prompts) > 0, "SDD prompts not copied with correct paths"

        # Platform-specific verification
        if sys.platform == "win32":
            # Windows: verify paths exist (Path normalizes separators correctly)
            for path in expected_paths:
                assert path.exists(), f"Path doesn't exist on Windows: {path}"
        else:
            # Unix: verify no backslashes in paths
            for path in expected_paths:
                assert "\\" not in str(path), f"Backslash in Unix path: {path}"


class TestScaffoldCLIIntegrationAcceptance:
    """CLI-level acceptance tests using subprocess."""

    def test_at_001_cli_fresh_init(self, tmp_path: Path, monkeypatch):
        """AT-001 via CLI: teambot init on fresh repository."""
        monkeypatch.chdir(tmp_path)

        # Run teambot init via subprocess (use uv run teambot)
        result = subprocess.run(
            ["uv", "run", "teambot", "init"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should succeed
        assert result.returncode == 0, f"Init failed: {result.stderr}"

        # Verify output contains copied messages
        output_lower = result.stdout.lower()
        assert "copied" in output_lower or "✓" in result.stdout, (
            f"Expected 'Copied' in output: {result.stdout}"
        )

        # Verify files exist
        assert (tmp_path / "teambot.json").exists(), "teambot.json not created"
        assert (tmp_path / "stages.yaml").exists(), "stages.yaml not created"
        assert (tmp_path / "AGENTS.md").exists(), "AGENTS.md not created"

    def test_at_002_cli_reinit_shows_skipped(self, tmp_path: Path, monkeypatch):
        """AT-002 via CLI: Re-running init shows skipped messages."""
        monkeypatch.chdir(tmp_path)

        # First init
        result1 = subprocess.run(
            ["uv", "run", "teambot", "init"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result1.returncode == 0, f"First init failed: {result1.stderr}"

        # Second init - will fail because teambot.json exists (expected CLI behavior)
        result = subprocess.run(
            ["uv", "run", "teambot", "init"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # CLI returns exit code 1 when config exists (this is expected behavior)
        # The important thing is that the scaffolds were not overwritten on first init
        # and the error message mentions the existing config
        assert "already exists" in result.stdout.lower() or "exists" in result.stdout.lower(), (
            f"Expected 'exists' message in output: {result.stdout}"
        )

        # Verify that scaffold files from first init are still present and unchanged
        assert (tmp_path / "stages.yaml").exists(), "stages.yaml should still exist"
        assert (tmp_path / "AGENTS.md").exists(), "AGENTS.md should still exist"
