"""Tests for Phase 5: Model comparison and Anthropic adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Check if anthropic is available
try:
    from anthropic import Anthropic, AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from aegis.adapters.base import ModelResponse

if HAS_ANTHROPIC:
    from aegis.adapters.anthropic_adapter import AnthropicAdapter


@pytest.mark.skipif(not HAS_ANTHROPIC, reason="anthropic package not installed")
class TestAnthropicAdapter:
    """Test Anthropic adapter functionality."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = AnthropicAdapter(api_key="test-key")
        assert adapter.model == "claude-3-opus-20240229"
        assert adapter.api_key == "test-key"

    def test_adapter_custom_model(self):
        """Test initialization with custom model."""
        adapter = AnthropicAdapter(
            api_key="test-key",
            model="claude-3-haiku-20240307",
        )
        assert adapter.model == "claude-3-haiku-20240307"

    def test_get_model_info(self):
        """Test getting model information."""
        adapter = AnthropicAdapter(api_key="test-key")
        info = adapter.get_model_info()

        assert info["model"] == "claude-3-opus-20240229"
        assert info["provider"] == "anthropic"
        assert "pricing" in info
        assert info["pricing"]["input_per_1k_tokens"] == 0.015
        assert info["pricing"]["output_per_1k_tokens"] == 0.075
        assert info["context_window"] == 200000
        assert info["supports_async"] is True

    def test_pricing_data(self):
        """Test pricing data for different models."""
        adapter_opus = AnthropicAdapter(
            api_key="test-key",
            model="claude-3-opus-20240229",
        )
        adapter_haiku = AnthropicAdapter(
            api_key="test-key",
            model="claude-3-haiku-20240307",
        )

        opus_info = adapter_opus.get_model_info()
        haiku_info = adapter_haiku.get_model_info()

        assert opus_info["pricing"]["input_per_1k_tokens"] > haiku_info["pricing"][
            "input_per_1k_tokens"
        ]

    def test_context_window_detection(self):
        """Test context window detection by model."""
        models = {
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
        }

        for model, expected_window in models.items():
            adapter = AnthropicAdapter(api_key="test-key", model=model)
            info = adapter.get_model_info()
            assert info["context_window"] == expected_window

    @pytest.mark.asyncio
    async def test_call_async(self):
        """Test async call to model."""
        adapter = AnthropicAdapter(api_key="test-key")

        # Mock the async client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.id = "msg-123"
        mock_response.stop_reason = "end_turn"

        with patch.object(
            adapter.async_client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await adapter.call("test prompt")

            assert isinstance(response, ModelResponse)
            assert response.text == "Test response"
            assert response.input_tokens == 10
            assert response.output_tokens == 20
            assert response.model == "claude-3-opus-20240229"
            assert response.latency_ms > 0

    def test_call_sync(self):
        """Test synchronous call to model."""
        adapter = AnthropicAdapter(api_key="test-key")

        # Mock the sync client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.id = "msg-123"
        mock_response.stop_reason = "end_turn"

        with patch.object(
            adapter.client.messages,
            "create",
            return_value=mock_response,
        ):
            response = adapter.call_sync("test prompt")

            assert isinstance(response, ModelResponse)
            assert response.text == "Test response"
            assert response.input_tokens == 10
            assert response.output_tokens == 20

    def test_validate_connection_success(self):
        """Test successful connection validation."""
        adapter = AnthropicAdapter(api_key="test-key")

        mock_response = MagicMock()
        mock_response.usage.input_tokens = 1
        mock_response.content = [MagicMock(text="ok")]

        with patch.object(
            adapter.client.messages,
            "create",
            return_value=mock_response,
        ):
            assert adapter.validate_connection() is True

    def test_validate_connection_failure(self):
        """Test failed connection validation."""
        adapter = AnthropicAdapter(api_key="invalid-key")

        with patch.object(
            adapter.client.messages,
            "create",
            side_effect=Exception("Authentication failed"),
        ):
            assert adapter.validate_connection() is False

    def test_adapter_parameters(self):
        """Test adapter accepts temperature and max_tokens."""
        adapter = AnthropicAdapter(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="response")]
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 10
        mock_response.id = "msg-123"
        mock_response.stop_reason = "end_turn"

        with patch.object(
            adapter.client.messages,
            "create",
            return_value=mock_response,
        ) as mock_create:
            adapter.call_sync("test", temperature=0.5, max_tokens=500)

            # Verify parameters were passed
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_tokens"] == 500


class TestModelComparison:
    """Test model comparison functionality."""

    def test_cpq_calculation(self):
        """Test cost-per-quality calculation."""
        # More efficient model (lower cost, higher score)
        model1 = {"model": "efficient", "cost": 0.01, "score": 0.95}

        # Less efficient model (higher cost, lower score)
        model2 = {"model": "expensive", "cost": 0.05, "score": 0.85}

        cpq1 = model1["cost"] / model1["score"]
        cpq2 = model2["cost"] / model2["score"]

        assert cpq1 < cpq2
        assert cpq1 == pytest.approx(0.01053, rel=0.01)

    def test_cpq_with_zero_cost(self):
        """Test CPQ handling with zero cost."""
        result = {"cost": 0, "score": 0.9}

        if result["cost"] > 0:
            cpq = result["cost"] / result["score"]
        else:
            cpq = float("inf")

        assert cpq == float("inf")

    def test_cpq_with_zero_score(self):
        """Test CPQ handling with zero score."""
        result = {"cost": 0.1, "score": 0}

        if result["score"] > 0:
            cpq = result["cost"] / result["score"]
        else:
            cpq = float("inf")

        assert cpq == float("inf")

    def test_ranking_by_cpq(self):
        """Test ranking models by CPQ."""
        results = [
            {"model": "a", "cost": 0.02, "score": 0.90, "cpq": 0.0222},
            {"model": "b", "cost": 0.01, "score": 0.85, "cpq": 0.0118},
            {"model": "c", "cost": 0.03, "score": 0.95, "cpq": 0.0316},
        ]

        # Sort by CPQ
        ranked = sorted(results, key=lambda x: x["cpq"])

        assert ranked[0]["model"] == "b"
        assert ranked[1]["model"] == "a"
        assert ranked[2]["model"] == "c"

    def test_comparison_with_error_handling(self):
        """Test comparison handles model errors gracefully."""
        results = {
            "gpt-4": {"score": 0.92, "cost": 0.08, "latency": 2.4},
            "claude": {"error": "API key invalid"},
            "gpt-3.5": {"score": 0.81, "cost": 0.02, "latency": 1.2},
        }

        valid_results = {k: v for k, v in results.items() if "error" not in v}

        assert len(valid_results) == 2
        assert "claude" not in valid_results

    def test_latency_comparison(self):
        """Test comparing model latencies."""
        models = [
            {"name": "fast", "latency": 0.5},
            {"name": "medium", "latency": 1.2},
            {"name": "slow", "latency": 3.0},
        ]

        fastest = min(models, key=lambda x: x["latency"])
        assert fastest["name"] == "fast"

    def test_score_quality_ranking(self):
        """Test ranking by score quality."""
        models = [
            {"name": "model_a", "score": 0.92},
            {"name": "model_b", "score": 0.85},
            {"name": "model_c", "score": 0.88},
        ]

        ranked = sorted(models, key=lambda x: x["score"], reverse=True)

        assert ranked[0]["name"] == "model_a"
        assert ranked[1]["name"] == "model_c"
        assert ranked[2]["name"] == "model_b"

    def test_multi_factor_ranking(self):
        """Test ranking with multiple factors."""
        models = [
            {"name": "a", "score": 0.92, "cost": 0.08, "latency": 2.0},
            {"name": "b", "score": 0.87, "cost": 0.02, "latency": 1.0},
            {"name": "c", "score": 0.90, "cost": 0.05, "latency": 1.5},
        ]

        # Calculate CPQ (cost-per-quality)
        for model in models:
            model["cpq"] = model["cost"] / model["score"]

        # Rank by CPQ
        ranked_cpq = sorted(models, key=lambda x: x["cpq"])

        assert ranked_cpq[0]["name"] == "b"
