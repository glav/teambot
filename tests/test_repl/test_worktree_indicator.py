"""Tests for REPL prompt worktree indicator."""

import pytest


class TestREPLPromptWorktreeIndicator:
    """Tests for worktree indicator in REPL prompt."""

    def test_repl_loop_init_accepts_worktree_context(self):
        """REPLLoop accepts worktree_context parameter."""
        from teambot.repl.loop import REPLLoop

        # Should not raise
        repl = REPLLoop(worktree_context=None)
        assert repl._worktree_context is None

    def test_repl_loop_stores_worktree_context(self, tmp_path):
        """REPLLoop stores worktree_context."""
        from teambot.repl.loop import REPLLoop
        from teambot.worktree.manager import WorktreeContext

        context = WorktreeContext(
            worktree_path=tmp_path,
            branch_name="feat/test",
            repo_root=tmp_path.parent,
        )

        repl = REPLLoop(worktree_context=context)
        assert repl._worktree_context is context
        assert repl._worktree_context.branch_name == "feat/test"


class TestRunInteractiveModeWorktree:
    """Tests for run_interactive_mode with worktree_context."""

    @pytest.mark.asyncio
    async def test_run_interactive_mode_accepts_worktree_context(self, mocker):
        """run_interactive_mode accepts worktree_context parameter."""
        from teambot.repl import run_interactive_mode

        # Mock REPLLoop to avoid actual execution
        mock_repl_class = mocker.patch("teambot.repl.loop.REPLLoop")
        mock_repl_instance = mocker.MagicMock()
        mock_repl_class.return_value = mock_repl_instance

        # Mock run to return immediately
        async def mock_run():
            pass

        mock_repl_instance.run = mock_run

        # Mock should_use_split_pane to force legacy mode (imported from ui.app)
        mocker.patch("teambot.ui.app.should_use_split_pane", return_value=False)
        mocker.patch.dict("os.environ", {"TEAMBOT_SPLIT_PANE": "false"})

        # Call with worktree_context
        from pathlib import Path

        from teambot.worktree.manager import WorktreeContext

        context = WorktreeContext(
            worktree_path=Path("/tmp/wt"),
            branch_name="feat/test",
            repo_root=Path("/tmp"),
        )

        await run_interactive_mode(worktree_context=context)

        # Verify REPLLoop was called with worktree_context
        mock_repl_class.assert_called_once()
        call_kwargs = mock_repl_class.call_args[1]
        assert call_kwargs.get("worktree_context") is context
