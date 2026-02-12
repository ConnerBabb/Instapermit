from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_products():
    """Reusable list of product dicts matching the scraper output schema."""
    return [
        {
            "title": "Gaming Laptop 15.6 inch",
            "price": "$999.99",
            "rating": 4.5,
            "url": "https://example.com/product/1",
        },
        {
            "title": "Budget Wireless Mouse",
            "price": "$12.99",
            "rating": 3.8,
            "url": "https://example.com/product/2",
        },
    ]


@pytest.fixture
def mock_openai_response():
    """Factory fixture that creates a mock requests.Response for OpenAI API calls."""

    def _make(content: str, status_code: int = 200):
        resp = MagicMock()
        resp.status_code = status_code
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"choices": [{"message": {"content": content}}]}
        return resp

    return _make
