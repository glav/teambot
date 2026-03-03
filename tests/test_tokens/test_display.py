"""Tests for token usage display functions.

Code-First tests: Functions implemented first, then tests added for structural validation.
"""

from rich.panel import Panel

from teambot.tokens.display import render_session_summary, render_token_summary
from teambot.tokens.models import TokenUsage


class TestRenderTokenSummary:
    """Tests for render_token_summary function."""

    def test_render_summary_panel_structure(self):
        """Panel has correct type and title."""
        total = TokenUsage(input_tokens=100, output_tokens=200)
        by_agent = {"pm": TokenUsage(input_tokens=100, output_tokens=200)}

        result = render_token_summary(total, by_agent)

        assert isinstance(result, Panel)
        assert result.title is not None
        assert "Token Usage" in str(result.title)

    def test_render_summary_with_data(self):
        """Panel shows actual token values when data is available."""
        total = TokenUsage(input_tokens=1500, output_tokens=2500)
        by_agent = {
            "pm": TokenUsage(input_tokens=500, output_tokens=800),
            "builder-1": TokenUsage(input_tokens=1000, output_tokens=1700),
        }

        result = render_token_summary(total, by_agent)

        # Panel renderable contains the text content
        content = str(result.renderable)
        assert "4,000" in content  # total tokens
        assert "1,500" in content  # prompt tokens
        assert "2,500" in content  # completion tokens

    def test_render_summary_unavailable(self):
        """Panel shows 'n/a' when token data is unavailable."""
        total = TokenUsage()  # All None
        by_agent = {}

        result = render_token_summary(total, by_agent)

        content = str(result.renderable)
        assert "n/a" in content
        assert "unavailable" in content

    def test_render_summary_per_agent_breakdown(self):
        """Panel includes per-agent breakdown section."""
        total = TokenUsage(input_tokens=100, output_tokens=200)
        by_agent = {
            "pm": TokenUsage(input_tokens=50, output_tokens=100),
            "reviewer": TokenUsage(input_tokens=50, output_tokens=100),
        }

        result = render_token_summary(total, by_agent)

        content = str(result.renderable)
        assert "pm" in content
        assert "reviewer" in content
        assert "By Agent" in content

    def test_render_summary_per_stage_breakdown(self):
        """Panel includes per-stage breakdown when provided."""
        total = TokenUsage(input_tokens=100, output_tokens=200)
        by_agent = {"pm": TokenUsage(input_tokens=100, output_tokens=200)}
        by_stage = {
            "PLAN": TokenUsage(input_tokens=50, output_tokens=100),
            "IMPLEMENTATION": TokenUsage(input_tokens=50, output_tokens=100),
        }

        result = render_token_summary(total, by_agent, by_stage)

        content = str(result.renderable)
        assert "PLAN" in content
        assert "IMPLEMENTATION" in content
        assert "By Stage" in content

    def test_render_summary_without_stage(self):
        """Panel works without stage breakdown."""
        total = TokenUsage(input_tokens=100, output_tokens=200)
        by_agent = {"pm": TokenUsage(input_tokens=100, output_tokens=200)}

        result = render_token_summary(total, by_agent, by_stage=None)

        content = str(result.renderable)
        assert "By Stage" not in content

    def test_render_summary_sorted_by_usage(self):
        """Agents sorted by token usage descending."""
        total = TokenUsage(input_tokens=300, output_tokens=600)
        by_agent = {
            "reviewer": TokenUsage(input_tokens=50, output_tokens=50),  # 100
            "pm": TokenUsage(input_tokens=200, output_tokens=400),  # 600
            "ba": TokenUsage(input_tokens=50, output_tokens=150),  # 200
        }

        result = render_token_summary(total, by_agent)

        content = str(result.renderable)
        # pm (600) should appear before ba (200) which should appear before reviewer (100)
        pm_pos = content.find("pm")
        ba_pos = content.find("ba")
        reviewer_pos = content.find("reviewer")
        assert pm_pos < ba_pos < reviewer_pos


class TestRenderSessionSummary:
    """Tests for render_session_summary function."""

    def test_render_session_summary_format(self):
        """Session summary has correct format with token counts."""
        total = TokenUsage(input_tokens=500, output_tokens=1000)

        result = render_session_summary(total)

        assert isinstance(result, str)
        assert "Session Token Usage:" in result
        assert "1,500" in result  # total
        assert "prompt:" in result
        assert "completion:" in result

    def test_render_session_summary_unavailable(self):
        """Session summary shows 'n/a' when unavailable."""
        total = TokenUsage()  # All None

        result = render_session_summary(total)

        assert "n/a" in result
        assert "Session Token Usage:" in result

    def test_render_session_summary_only_total(self):
        """Session summary works with only total_tokens computed."""
        # If only one of input/output is set, total_tokens will be that value
        total = TokenUsage(input_tokens=500, output_tokens=None)

        result = render_session_summary(total)

        assert "500" in result
        # Without both, shouldn't show breakdown
        assert "prompt:" not in result

    def test_render_session_summary_zero_tokens(self):
        """Session summary handles zero tokens correctly."""
        total = TokenUsage(input_tokens=0, output_tokens=0)

        result = render_session_summary(total)

        assert "0 tokens" in result
