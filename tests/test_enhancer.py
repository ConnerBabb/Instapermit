import copy
from unittest.mock import MagicMock, patch

import requests

from enhancer import (
    _chat,
    categorize_products,
    enhance_products,
    suggest_selector,
    summarize_ratings,
)

# ── _chat ────────────────────────────────────────────────────────────────────


class TestChat:
    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_success(self, mock_post, mock_openai_response):
        mock_post.return_value = mock_openai_response("Hello from AI")
        result = _chat("system prompt", "user prompt")
        assert result == "Hello from AI"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "Bearer sk-test-key" in str(call_kwargs)

    @patch("enhancer.OPENAI_API_KEY", "")
    def test_no_api_key_raises(self):
        try:
            _chat("system", "user")
            assert False, "Should have raised EnvironmentError"
        except EnvironmentError as e:
            assert "OPENAI_API_KEY" in str(e)

    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_http_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_resp

        try:
            _chat("system", "user")
            assert False, "Should have raised HTTPError"
        except requests.HTTPError:
            pass


# ── categorize_products ──────────────────────────────────────────────────────


class TestCategorizeProducts:
    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_success(self, mock_post, sample_products, mock_openai_response):
        products = copy.deepcopy(sample_products)
        mock_post.return_value = mock_openai_response('["gaming", "budget"]')

        result = categorize_products(products)
        assert result[0]["ai_category"] == "gaming"
        assert result[1]["ai_category"] == "budget"

    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_json_parse_error_defaults_to_general(
        self, mock_post, sample_products, mock_openai_response
    ):
        products = copy.deepcopy(sample_products)
        mock_post.return_value = mock_openai_response("not valid json")

        result = categorize_products(products)
        assert result[0]["ai_category"] == "general"
        assert result[1]["ai_category"] == "general"


# ── summarize_ratings ────────────────────────────────────────────────────────


class TestSummarizeRatings:
    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_success(self, mock_post, sample_products, mock_openai_response):
        products = copy.deepcopy(sample_products)
        sentiments = '["Great laptop!", "Decent mouse."]'
        mock_post.return_value = mock_openai_response(sentiments)

        result = summarize_ratings(products)
        assert result[0]["ai_sentiment"] == "Great laptop!"
        assert result[1]["ai_sentiment"] == "Decent mouse."

    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_json_parse_error_defaults(self, mock_post, sample_products, mock_openai_response):
        products = copy.deepcopy(sample_products)
        mock_post.return_value = mock_openai_response("invalid json")

        result = summarize_ratings(products)
        assert result[0]["ai_sentiment"] == "No sentiment available."
        assert result[1]["ai_sentiment"] == "No sentiment available."


# ── suggest_selector ─────────────────────────────────────────────────────────


class TestSuggestSelector:
    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_returns_selector(self, mock_post, mock_openai_response):
        mock_post.return_value = mock_openai_response("h2.product-title a")
        html = "<div><h2 class='product-title'><a>Link</a></h2></div>"
        result = suggest_selector("h2.old a", html)
        assert result == "h2.product-title a"


# ── enhance_products ─────────────────────────────────────────────────────────


class TestEnhanceProducts:
    @patch("enhancer.OPENAI_API_KEY", "")
    def test_no_api_key_graceful_degradation(self, sample_products):
        products = copy.deepcopy(sample_products)
        result = enhance_products(products)
        assert result[0]["ai_category"] == "unknown (no API key)"
        assert result[0]["ai_sentiment"] == "unavailable (no API key)"

    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_full_enhancement(self, mock_post, sample_products, mock_openai_response):
        products = copy.deepcopy(sample_products)
        # First call: categorize_products, second call: summarize_ratings
        mock_post.side_effect = [
            mock_openai_response('["gaming", "budget"]'),
            mock_openai_response('["Great laptop!", "Decent mouse."]'),
        ]

        result = enhance_products(products)
        assert result[0]["ai_category"] == "gaming"
        assert result[1]["ai_sentiment"] == "Decent mouse."

    @patch("enhancer.OPENAI_API_KEY", "sk-test-key")
    @patch("enhancer.requests.post")
    def test_partial_failure_still_returns(self, mock_post, sample_products, mock_openai_response):
        """If categorization succeeds but sentiment fails, products still returned."""
        products = copy.deepcopy(sample_products)
        mock_post.side_effect = [
            mock_openai_response('["gaming", "budget"]'),
            requests.HTTPError("API error"),
        ]

        result = enhance_products(products)
        # Categorization should have been applied
        assert result[0]["ai_category"] == "gaming"
        # Products are still returned even though sentiment failed
        assert len(result) == 2
