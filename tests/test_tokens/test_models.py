"""Tests for TokenUsage dataclass."""


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_create_with_all_fields(self):
        """TokenUsage can be created with all fields populated."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=10,
            cache_write_tokens=5,
        )

        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.cache_read_tokens == 10
        assert usage.cache_write_tokens == 5

    def test_create_with_none_fields(self):
        """TokenUsage can be created with all fields None (unavailable)."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage()

        assert usage.input_tokens is None
        assert usage.output_tokens is None
        assert usage.cache_read_tokens is None
        assert usage.cache_write_tokens is None

    def test_create_with_partial_data(self):
        """TokenUsage allows partial data (some fields populated)."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(
            input_tokens=100,
            output_tokens=None,
        )

        assert usage.input_tokens == 100
        assert usage.output_tokens is None
        assert usage.cache_read_tokens is None

    def test_total_tokens_calculation(self):
        """total_tokens returns sum of input + output."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(input_tokens=100, output_tokens=50)

        assert usage.total_tokens == 150

    def test_total_tokens_when_one_is_none(self):
        """total_tokens handles one value being None."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(input_tokens=100, output_tokens=None)

        # When one is None, total should still work with partial data
        assert usage.total_tokens == 100

    def test_total_tokens_when_both_none(self):
        """total_tokens returns None when both input and output are None."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage()

        assert usage.total_tokens is None

    def test_to_dict_serialization(self):
        """to_dict produces JSON-serializable dict."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=10,
            cache_write_tokens=5,
        )

        result = usage.to_dict()

        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["cache_read_tokens"] == 10
        assert result["cache_write_tokens"] == 5
        assert result["total_tokens"] == 150

    def test_to_dict_with_none_values(self):
        """to_dict handles None values correctly."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage()

        result = usage.to_dict()

        assert result["input_tokens"] is None
        assert result["output_tokens"] is None
        assert result["total_tokens"] is None

    def test_from_dict_deserialization(self):
        """from_dict creates TokenUsage from dict."""
        from teambot.tokens.models import TokenUsage

        data = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_tokens": 10,
            "cache_write_tokens": 5,
        }

        usage = TokenUsage.from_dict(data)

        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.cache_read_tokens == 10
        assert usage.cache_write_tokens == 5

    def test_from_dict_with_missing_keys(self):
        """from_dict handles missing keys gracefully."""
        from teambot.tokens.models import TokenUsage

        data = {"input_tokens": 100}

        usage = TokenUsage.from_dict(data)

        assert usage.input_tokens == 100
        assert usage.output_tokens is None
        assert usage.cache_read_tokens is None

    def test_from_dict_empty(self):
        """from_dict handles empty dict."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage.from_dict({})

        assert usage.input_tokens is None
        assert usage.output_tokens is None

    def test_from_sdk_usage(self):
        """from_sdk_usage creates TokenUsage from SDK Usage object."""
        from dataclasses import dataclass

        from teambot.tokens.models import TokenUsage

        # Mock SDK Usage dataclass
        @dataclass
        class MockSDKUsage:
            input_tokens: float
            output_tokens: float
            cache_read_tokens: float
            cache_write_tokens: float

        sdk_usage = MockSDKUsage(
            input_tokens=100.0,
            output_tokens=50.0,
            cache_read_tokens=10.0,
            cache_write_tokens=5.0,
        )

        usage = TokenUsage.from_sdk_usage(sdk_usage)

        # SDK uses float, we convert to int
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.cache_read_tokens == 10
        assert usage.cache_write_tokens == 5
        assert isinstance(usage.input_tokens, int)

    def test_from_sdk_usage_with_none_values(self):
        """from_sdk_usage handles None values from SDK."""
        from dataclasses import dataclass

        from teambot.tokens.models import TokenUsage

        @dataclass
        class MockSDKUsage:
            input_tokens: float | None
            output_tokens: float | None
            cache_read_tokens: float | None
            cache_write_tokens: float | None

        sdk_usage = MockSDKUsage(
            input_tokens=100.0,
            output_tokens=None,
            cache_read_tokens=None,
            cache_write_tokens=None,
        )

        usage = TokenUsage.from_sdk_usage(sdk_usage)

        assert usage.input_tokens == 100
        assert usage.output_tokens is None

    def test_from_sdk_usage_with_zero_values(self):
        """from_sdk_usage handles zero values correctly (0 is valid, not None)."""
        from dataclasses import dataclass

        from teambot.tokens.models import TokenUsage

        @dataclass
        class MockSDKUsage:
            input_tokens: float
            output_tokens: float
            cache_read_tokens: float
            cache_write_tokens: float

        sdk_usage = MockSDKUsage(
            input_tokens=0.0,
            output_tokens=0.0,
            cache_read_tokens=0.0,
            cache_write_tokens=0.0,
        )

        usage = TokenUsage.from_sdk_usage(sdk_usage)

        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_addition_operator(self):
        """TokenUsage + TokenUsage aggregates correctly."""
        from teambot.tokens.models import TokenUsage

        usage1 = TokenUsage(input_tokens=100, output_tokens=50)
        usage2 = TokenUsage(input_tokens=200, output_tokens=100)

        result = usage1 + usage2

        assert result.input_tokens == 300
        assert result.output_tokens == 150
        assert result.total_tokens == 450

    def test_addition_with_none_values(self):
        """Addition handles None values correctly."""
        from teambot.tokens.models import TokenUsage

        usage1 = TokenUsage(input_tokens=100, output_tokens=None)
        usage2 = TokenUsage(input_tokens=200, output_tokens=50)

        result = usage1 + usage2

        # 100 + 200 = 300; None + 50 = 50
        assert result.input_tokens == 300
        assert result.output_tokens == 50

    def test_addition_with_both_none(self):
        """Addition where both sides have None returns None."""
        from teambot.tokens.models import TokenUsage

        usage1 = TokenUsage(input_tokens=None, output_tokens=None)
        usage2 = TokenUsage(input_tokens=None, output_tokens=None)

        result = usage1 + usage2

        assert result.input_tokens is None
        assert result.output_tokens is None
        assert result.total_tokens is None

    def test_addition_all_cache_fields(self):
        """Addition aggregates all four token fields."""
        from teambot.tokens.models import TokenUsage

        usage1 = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=10,
            cache_write_tokens=5,
        )
        usage2 = TokenUsage(
            input_tokens=200,
            output_tokens=100,
            cache_read_tokens=20,
            cache_write_tokens=10,
        )

        result = usage1 + usage2

        assert result.input_tokens == 300
        assert result.output_tokens == 150
        assert result.cache_read_tokens == 30
        assert result.cache_write_tokens == 15

    def test_zero_tokens_valid(self):
        """Zero tokens is a valid state (different from None)."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(input_tokens=0, output_tokens=0)

        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0
        assert usage.total_tokens is not None
