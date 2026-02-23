"""Tests for branch name derivation."""

from pathlib import Path

import pytest

from teambot.worktree.manager import derive_branch_name


class TestBranchNameDerivation:
    """Tests for deriving branch names from objective filenames."""

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("my-feature.md", "feat/my-feature"),
            ("objective-foo.md", "feat/foo"),
            ("sdd-objective-auth.md", "feat/auth"),
            ("add-login-page.md", "feat/add-login-page"),
            ("fix-bug-123.md", "feat/fix-bug-123"),
            ("UPPER-CASE.md", "feat/upper-case"),
        ],
    )
    def test_derive_branch_name_patterns(self, filename, expected):
        """Branch name derived correctly from objective filename."""
        result = derive_branch_name(Path(filename))
        assert result == expected

    def test_derive_branch_name_strips_objective_prefix(self):
        """objective- prefix is stripped from filename."""
        result = derive_branch_name(Path("objective-my-feature.md"))
        assert result == "feat/my-feature"

    def test_derive_branch_name_strips_sdd_objective_prefix(self):
        """sdd-objective- prefix is stripped from filename."""
        result = derive_branch_name(Path("sdd-objective-auth.md"))
        assert result == "feat/auth"

    def test_derive_branch_name_explicit_override(self):
        """Explicit branch overrides derivation."""
        result = derive_branch_name(Path("foo.md"), explicit_branch="custom-branch")
        assert result == "feat/custom-branch"

    def test_derive_branch_name_explicit_with_prefix(self):
        """Explicit branch with prefix is preserved."""
        result = derive_branch_name(Path("foo.md"), explicit_branch="fix/bug-123")
        assert result == "fix/bug-123"

    def test_derive_branch_name_empty_after_strip(self):
        """Falls back to 'feature' if filename is empty after stripping."""
        result = derive_branch_name(Path("objective.md"))
        assert result == "feat/feature"

    def test_derive_branch_name_special_chars_removed(self):
        """Special characters are removed from branch name."""
        result = derive_branch_name(Path("my_feature@v2.md"))
        assert result == "feat/myfeaturev2"

    def test_derive_branch_name_spaces_to_hyphens(self):
        """Spaces are converted to hyphens."""
        result = derive_branch_name(Path("my feature name.md"))
        assert result == "feat/my-feature-name"

    def test_derive_branch_name_with_path(self):
        """Works with full path, not just filename."""
        result = derive_branch_name(Path("/some/path/objectives/my-feature.md"))
        assert result == "feat/my-feature"

    def test_derive_branch_name_consecutive_hyphens_collapsed(self):
        """Consecutive hyphens are collapsed to single hyphen."""
        result = derive_branch_name(Path("my--feature--name.md"))
        assert result == "feat/my-feature-name"

    def test_derive_branch_name_leading_trailing_hyphens_removed(self):
        """Leading and trailing hyphens are removed."""
        result = derive_branch_name(Path("-my-feature-.md"))
        assert result == "feat/my-feature"
