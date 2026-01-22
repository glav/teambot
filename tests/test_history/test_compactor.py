"""Tests for context compactor - TDD approach."""


class TestTokenEstimator:
    """Tests for token estimation."""

    def test_estimate_tokens_basic(self):
        """Estimate tokens for basic text."""
        from teambot.history.compactor import estimate_tokens

        text = "Hello world"
        tokens = estimate_tokens(text)

        # Rough estimate: ~4 chars per token
        assert 2 <= tokens <= 5

    def test_estimate_tokens_code(self):
        """Estimate tokens for code content."""
        from teambot.history.compactor import estimate_tokens

        code = """
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
"""
        tokens = estimate_tokens(code)
        assert tokens > 0


class TestContextCompactor:
    """Tests for ContextCompactor class."""

    def test_create_compactor(self):
        """Compactor initializes with default limits."""
        from teambot.history.compactor import ContextCompactor

        compactor = ContextCompactor()

        assert compactor.max_tokens == 150000  # Default limit
        assert compactor.warning_threshold == 0.8

    def test_create_compactor_custom_limit(self):
        """Compactor accepts custom token limit."""
        from teambot.history.compactor import ContextCompactor

        compactor = ContextCompactor(max_tokens=100000)

        assert compactor.max_tokens == 100000

    def test_check_context_size_under_threshold(self):
        """Content under threshold returns OK status."""
        from teambot.history.compactor import ContextCompactor, ContextStatus

        compactor = ContextCompactor(max_tokens=1000)
        content = "Short content"

        status = compactor.check_context_size(content)

        assert status == ContextStatus.OK

    def test_check_context_size_warning(self):
        """Content at 80%+ threshold returns WARNING."""
        from teambot.history.compactor import ContextCompactor, ContextStatus

        compactor = ContextCompactor(max_tokens=100, warning_threshold=0.8)
        # Generate content that's ~85% of limit (85 tokens = 340 chars at 4 chars/token)
        content = "x" * 340  # 340/4 = 85 tokens, 85% of 100

        status = compactor.check_context_size(content)

        assert status == ContextStatus.WARNING

    def test_check_context_size_critical(self):
        """Content over limit returns CRITICAL."""
        from teambot.history.compactor import ContextCompactor, ContextStatus

        compactor = ContextCompactor(max_tokens=50)
        # Generate content that's way over limit
        content = "word " * 200

        status = compactor.check_context_size(content)

        assert status == ContextStatus.CRITICAL

    def test_compact_little(self):
        """Little compaction removes verbose sections."""
        from teambot.history.compactor import CompactionLevel, ContextCompactor

        compactor = ContextCompactor()
        content = """# Title

## Summary
This is the main summary.

## Details
These are the detailed explanation that can be trimmed.
More details here.
Even more details.

## Conclusion
Final thoughts.
"""
        result = compactor.compact(content, CompactionLevel.LITTLE)

        # Should still contain key sections
        assert "Title" in result
        assert "Summary" in result
        # Length should be reduced
        assert len(result) <= len(content)

    def test_compact_medium(self):
        """Medium compaction keeps only essential info."""
        from teambot.history.compactor import CompactionLevel, ContextCompactor

        compactor = ContextCompactor()
        content = """# Feature Implementation

## Summary
Implemented user authentication module.

## Changes Made
- Added login endpoint
- Added logout endpoint
- Added session management
- Added token validation
- Added password hashing

## Technical Details
The implementation uses JWT tokens with RS256 signing.
Tokens expire after 24 hours.
Refresh tokens are stored in HTTP-only cookies.

## Testing
All tests pass.
"""
        result = compactor.compact(content, CompactionLevel.MEDIUM)

        assert len(result) < len(content)
        # Should keep title and summary
        assert "Feature Implementation" in result or "authentication" in result.lower()

    def test_compact_high(self):
        """High compaction produces minimal summary."""
        from teambot.history.compactor import CompactionLevel, ContextCompactor

        compactor = ContextCompactor()
        content = (
            """# Very Long Document

This is the first paragraph with important summary.

## Section 1
"""
            + "Detailed content. " * 100
            + """

## Section 2
"""
            + "More content. " * 100
        )

        result = compactor.compact(content, CompactionLevel.HIGH)

        # Should be significantly shorter
        assert len(result) < len(content) * 0.5

    def test_get_compaction_recommendation(self):
        """Get recommended compaction level based on size."""
        from teambot.history.compactor import CompactionLevel, ContextCompactor

        compactor = ContextCompactor(max_tokens=100)

        # Under warning threshold - no compaction needed
        level = compactor.get_compaction_recommendation("short")
        assert level is None

        # At warning threshold - little compaction (85% = 340 chars)
        content_85 = "x" * 340
        level = compactor.get_compaction_recommendation(content_85)
        assert level == CompactionLevel.LITTLE

        # Over limit - high compaction (>100 tokens = >400 chars)
        content_over = "x" * 500
        level = compactor.get_compaction_recommendation(content_over)
        assert level == CompactionLevel.HIGH
