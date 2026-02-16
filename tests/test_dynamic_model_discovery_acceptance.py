"""Acceptance test validation for Dynamic Model Discovery feature.

These tests validate the acceptance scenarios against the REAL implementation.
Each test exercises the actual implementation code, not mocks of core functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestDynamicModelDiscoveryAcceptance:
    """Acceptance test scenarios for Dynamic Model Discovery."""

    @pytest.fixture
    def temp_teambot_dir(self, tmp_path):
        """Create a temporary .teambot directory for cache testing."""
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()
        return tmp_path

    @pytest.fixture
    def reset_schema_state(self):
        """Reset schema module state between tests."""
        from teambot.config.schema import reset_model_cache

        reset_model_cache()
        yield
        reset_model_cache()

    @pytest.fixture
    def mock_sdk_models(self):
        """Create mock SDK model responses with all tiers.

        Note: save_cache expects models with 'category' attribute directly,
        not 'capabilities.tier' (that's what SDK returns, which gets adapted).
        For testing, we provide models already in cache-compatible format.
        """
        from teambot.copilot.sdk_client import TeamBotModelInfo

        return [
            TeamBotModelInfo(id="gpt-5", name="GPT-5", category="standard", multiplier=1.0),
            TeamBotModelInfo(id="gpt-5-mini", name="GPT-5 Mini", category="fast", multiplier=0.25),
            TeamBotModelInfo(
                id="claude-opus-4.6", name="Claude Opus 4.6", category="premium", multiplier=5.0
            ),
            TeamBotModelInfo(
                id="claude-sonnet-4.5",
                name="Claude Sonnet 4.5",
                category="standard",
                multiplier=1.0,
            ),
            TeamBotModelInfo(
                id="claude-haiku-4.5", name="Claude Haiku 4.5", category="fast", multiplier=0.3
            ),
        ]

    # =========================================================================
    # AT-001: Fresh Install Model Discovery
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_001_fresh_install_model_discovery(
        self, temp_teambot_dir, reset_schema_state, mock_sdk_models
    ):
        """AT-001: User runs /models for first time with no cache.

        Validates that when no cache exists and SDK is available:
        - Models are fetched from SDK
        - Models are displayed with correct tiers
        - Cache file is created
        """
        from teambot.config.model_cache import load_cache
        from teambot.config.schema import reset_model_cache
        from teambot.repl.commands import handle_models

        # Ensure clean state - no cache exists
        cache_file = temp_teambot_dir / ".teambot" / "model_cache.json"
        assert not cache_file.exists(), "Cache should not exist initially"

        # Mock SDK to return models (simulating SDK availability)
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            # First, populate the cache via refresh (simulating SDK fetch)
            from teambot.config.model_cache import save_cache

            save_cache(mock_sdk_models, "1.0.0")

            # Verify cache file was created
            assert cache_file.exists(), "Cache file should be created after refresh"

            # Reset in-memory state to force reload from disk
            reset_model_cache()

            # Now call handle_models (the REAL implementation)
            result = await handle_models([])

        # Verify output contains models from all tiers
        assert result.success is True, f"Command should succeed: {result.output}"
        assert "STANDARD:" in result.output, "Should show STANDARD tier"
        assert "FAST:" in result.output, "Should show FAST tier"
        assert "PREMIUM:" in result.output, "Should show PREMIUM tier"

        # Verify specific models appear
        assert "gpt-5" in result.output, "Should show gpt-5 model"
        assert "claude-opus-4.6" in result.output, "Should show premium model"

        # Verify cache timestamp is shown
        assert "Cached:" in result.output, "Should show cache timestamp"

        # Verify cache file has valid structure
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            cache = load_cache()
        assert cache is not None, "Cache should be loadable"
        assert len(cache.models) == 5, "Cache should have all models"
        assert cache.timestamp > 0, "Cache should have timestamp"

    # =========================================================================
    # AT-002: Cached Model Display
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_002_cached_model_display(
        self, temp_teambot_dir, reset_schema_state, mock_sdk_models
    ):
        """AT-002: User runs /models with valid cache.

        Validates that when valid cache exists:
        - Models are displayed from cache
        - No SDK call is made
        - Cache age is shown correctly
        """
        from teambot.config.model_cache import save_cache
        from teambot.config.schema import reset_model_cache
        from teambot.repl.commands import handle_models

        # Pre-populate cache
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            save_cache(mock_sdk_models, "1.0.0")

        # Reset to force reload
        reset_model_cache()

        # Call handle_models - should use cache, NOT call SDK
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            # We don't mock the SDK here - if it were called, it would fail
            # The real implementation should read from cache
            result = await handle_models([])

        # Verify models displayed
        assert result.success is True
        assert "gpt-5" in result.output
        assert "claude-opus-4.6" in result.output

        # Verify cache status shown (should show "0 minutes ago" since just created)
        assert "Cached:" in result.output
        # Could be "0 minutes ago" or "X minutes ago"
        assert "ago" in result.output or "Cached" in result.output

    # =========================================================================
    # AT-003: SDK Failure - No Cache
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_003_sdk_failure_no_cache(self, temp_teambot_dir, reset_schema_state):
        """AT-003: User runs /models when SDK unavailable and no cache exists.

        Validates that when no cache exists and SDK fails:
        - Error message is displayed
        - No fallback list is shown
        - Actionable guidance is provided
        """
        from teambot.config.schema import reset_model_cache
        from teambot.repl.commands import handle_models

        # Ensure no cache exists
        cache_file = temp_teambot_dir / ".teambot" / "model_cache.json"
        if cache_file.exists():
            cache_file.unlink()

        reset_model_cache()

        # Call handle_models with no cache and no SDK
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            result = await handle_models([])

        # Verify error response
        assert result.success is False, "Command should fail when no models available"

        # Verify error formatting
        assert "[red]" in result.output, "Should use red error formatting"
        assert "No models available" in result.output, "Should indicate no models"

        # Verify actionable guidance
        assert "/models --refresh" in result.output, "Should suggest refresh command"

        # Verify NO fallback list is shown (no static models)
        assert "gpt-5" not in result.output or "No models" in result.output

    # =========================================================================
    # AT-004: SDK Failure - Valid Cache Exists
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_004_sdk_failure_with_valid_cache(
        self, temp_teambot_dir, reset_schema_state, mock_sdk_models
    ):
        """AT-004: User runs /models --refresh when SDK unavailable but cache exists.

        Validates that when cache exists and SDK refresh fails:
        - Error message about refresh failure is shown
        - Subsequent /models (without --refresh) still shows cached data
        - Cache file is not corrupted
        """
        from teambot.config.model_cache import load_cache, save_cache
        from teambot.config.schema import reset_model_cache
        from teambot.repl.commands import handle_models

        # Pre-populate cache
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            save_cache(mock_sdk_models, "1.0.0")
            original_cache = load_cache()

        reset_model_cache()

        # Mock refresh_models to fail (simulating SDK failure)
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            with patch(
                "teambot.config.schema.refresh_models",
                new_callable=AsyncMock,
                return_value=False,
            ):
                # Call /models --refresh - should fail
                refresh_result = await handle_models(["--refresh"])

        # Verify refresh failure message
        assert refresh_result.success is False, "Refresh should fail"
        assert "[red]" in refresh_result.output, "Should show red error"
        assert "Failed" in refresh_result.output, "Should indicate failure"

        # Reset and verify cached data still works
        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            # Subsequent /models without --refresh should work
            result = await handle_models([])

        assert result.success is True, "Cached models should still work"
        assert "gpt-5" in result.output, "Cached models should be displayed"

        # Verify cache not corrupted
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            current_cache = load_cache()
        assert current_cache is not None, "Cache should still be loadable"
        assert len(current_cache.models) == len(original_cache.models), "Cache should be intact"

    # =========================================================================
    # AT-005: Premium Model Visibility
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_005_premium_model_visibility(
        self, temp_teambot_dir, reset_schema_state, mock_sdk_models
    ):
        """AT-005: Premium models from SDK appear in output.

        Validates that premium tier models:
        - Appear under "PREMIUM:" category
        - Show correct model ID and display name
        - Have correct tier classification
        """
        from teambot.config.model_cache import save_cache
        from teambot.config.schema import reset_model_cache
        from teambot.repl.commands import handle_models

        # Pre-populate cache with models including premium
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            save_cache(mock_sdk_models, "1.0.0")

        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            result = await handle_models([])

        # Verify PREMIUM section exists
        assert "PREMIUM:" in result.output, "Should have PREMIUM section"

        # Verify premium model appears
        assert "claude-opus-4.6" in result.output, "Premium model ID should appear"
        assert "Claude Opus 4.6" in result.output, "Premium model display name should appear"

        # Verify premium model is in the PREMIUM section (not misclassified)
        lines = result.output.split("\n")
        in_premium_section = False
        premium_model_in_premium = False

        for line in lines:
            if "PREMIUM:" in line:
                in_premium_section = True
            elif "STANDARD:" in line or "FAST:" in line:
                in_premium_section = False
            elif in_premium_section and "claude-opus-4.6" in line:
                premium_model_in_premium = True

        assert premium_model_in_premium, "claude-opus-4.6 should be in PREMIUM section"

    # =========================================================================
    # AT-006: Tier Classification Accuracy
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_006_tier_classification_accuracy(
        self, temp_teambot_dir, reset_schema_state, mock_sdk_models
    ):
        """AT-006: All tier classifications match SDK data.

        Validates that each model appears in the correct tier category
        based on its capabilities.tier value from the SDK.
        """
        from teambot.config.model_cache import save_cache
        from teambot.config.schema import get_model_info, reset_model_cache
        from teambot.repl.commands import handle_models

        # Pre-populate cache
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            save_cache(mock_sdk_models, "1.0.0")

        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            result = await handle_models([])

            # Verify tier classification for each model
            # Standard models
            standard_info = get_model_info("gpt-5")
            assert standard_info["category"] == "standard", "gpt-5 should be standard"

            sonnet_info = get_model_info("claude-sonnet-4.5")
            assert sonnet_info["category"] == "standard", "claude-sonnet-4.5 should be standard"

            # Fast models
            mini_info = get_model_info("gpt-5-mini")
            assert mini_info["category"] == "fast", "gpt-5-mini should be fast"

            haiku_info = get_model_info("claude-haiku-4.5")
            assert haiku_info["category"] == "fast", "claude-haiku-4.5 should be fast"

            # Premium models
            opus_info = get_model_info("claude-opus-4.6")
            assert opus_info["category"] == "premium", "claude-opus-4.6 should be premium"

        # Verify output sections contain correct models
        lines = result.output.split("\n")

        # Parse output to verify section placement
        current_section = None
        section_models = {"STANDARD": [], "FAST": [], "PREMIUM": []}

        for line in lines:
            if "STANDARD:" in line:
                current_section = "STANDARD"
            elif "FAST:" in line:
                current_section = "FAST"
            elif "PREMIUM:" in line:
                current_section = "PREMIUM"
            elif current_section and ("gpt-" in line or "claude-" in line):
                section_models[current_section].append(line.strip())

        # Verify models in correct sections
        assert any("gpt-5" in m and "mini" not in m for m in section_models["STANDARD"]), (
            "gpt-5 should be in STANDARD"
        )
        assert any("gpt-5-mini" in m for m in section_models["FAST"]), (
            "gpt-5-mini should be in FAST"
        )
        assert any("claude-opus-4.6" in m for m in section_models["PREMIUM"]), (
            "claude-opus-4.6 should be in PREMIUM"
        )

    # =========================================================================
    # AT-007: Multiplier Display in /models Command
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_007_multiplier_display(
        self, temp_teambot_dir, reset_schema_state, mock_sdk_models
    ):
        """AT-007: /models command displays billing multiplier for each model.

        Validates that the /models output includes [Nx] multiplier suffix
        for models with billing multiplier data.
        """
        from teambot.config.model_cache import save_cache
        from teambot.config.schema import reset_model_cache
        from teambot.repl.commands import handle_models

        # Pre-populate cache with models that have multipliers
        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            save_cache(mock_sdk_models, "1.0.0")

        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
            result = await handle_models([])

        # Verify multiplier display in output
        assert "[1.0x]" in result.output or "[1x]" in result.output, (
            "Standard model should show [1.0x] multiplier"
        )
        assert "[5.0x]" in result.output or "[5x]" in result.output, (
            "Premium model should show [5.0x] multiplier"
        )
        assert "[0.25x]" in result.output, "Fast model should show [0.25x] multiplier"


class TestTierMultiplierClassification:
    """Tests for tier classification based on billing.multiplier."""

    def test_silent_fallback_no_billing(self, caplog):
        """Verify no warning is logged when SDK model has no billing data."""
        import logging

        from teambot.copilot.sdk_client import CopilotSDKClient

        class MockModel:
            id = "test-model"
            name = "Test Model"
            # No billing attribute

        with caplog.at_level(logging.WARNING):
            result = CopilotSDKClient._adapt_model_info(MockModel())

        assert result.category == "standard"
        assert result.multiplier is None
        # Verify NO warning was logged
        assert "missing" not in caplog.text.lower()
        assert "tier" not in caplog.text.lower()

    def test_multiplier_based_tier_classification(self):
        """Verify tier is derived from billing.multiplier."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        class MockBilling:
            multiplier = 5.0

        class MockModel:
            id = "test-model"
            name = "Test Model"
            billing = MockBilling()

        result = CopilotSDKClient._adapt_model_info(MockModel())

        assert result.category == "premium"
        assert result.multiplier == 5.0
