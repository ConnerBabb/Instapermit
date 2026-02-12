from unittest.mock import MagicMock, patch

import requests
from selenium.common.exceptions import TimeoutException, WebDriverException

from scraper import (
    _parse_amazon_card,
    create_driver,
    scrape_amazon,
    scrape_fakestoreapi,
    scrape_products,
)

# ── create_driver ────────────────────────────────────────────────────────────


class TestCreateDriver:
    @patch("scraper.ChromeDriverManager")
    @patch("scraper.webdriver.Chrome")
    def test_returns_chrome_driver(self, mock_chrome, mock_cdm):
        driver = create_driver()
        mock_chrome.assert_called_once()
        assert driver == mock_chrome.return_value


# ── _parse_amazon_card ───────────────────────────────────────────────────────


class TestParseAmazonCard:
    def _make_card(
        self,
        title="Test Product",
        price="$29.99",
        rating="4.2 out of 5",
        url="https://amazon.com/p",
    ):
        card = MagicMock()
        link_el = MagicMock()
        link_el.text = title
        link_el.get_attribute.return_value = url

        def find_element_side_effect(by, selector):
            if "h2" in selector:
                return link_el
            if "a-offscreen" in selector:
                el = MagicMock()
                el.text = price
                return el
            if "a-icon-alt" in selector:
                el = MagicMock()
                el.text = rating
                return el
            raise Exception("Element not found")

        card.find_element = MagicMock(side_effect=find_element_side_effect)
        return card

    def test_complete_card(self):
        card = self._make_card()
        result = _parse_amazon_card(card)
        assert result == {
            "title": "Test Product",
            "price": "$29.99",
            "rating": 4.2,
            "url": "https://amazon.com/p",
        }

    def test_missing_price(self):
        card = self._make_card()
        original_side_effect = card.find_element.side_effect

        def no_price(by, selector):
            if "a-offscreen" in selector:
                raise Exception("no price")
            return original_side_effect(by, selector)

        card.find_element.side_effect = no_price
        result = _parse_amazon_card(card)
        assert result is not None
        assert result["price"] is None
        assert result["title"] == "Test Product"

    def test_empty_title_returns_none(self):
        card = self._make_card(title="")
        result = _parse_amazon_card(card)
        assert result is None

    def test_link_element_exception_returns_none(self):
        card = MagicMock()
        card.find_element.side_effect = Exception("no link")
        result = _parse_amazon_card(card)
        assert result is None


# ── scrape_amazon ────────────────────────────────────────────────────────────


class TestScrapeAmazon:
    @patch("scraper.create_driver")
    def test_success(self, mock_create_driver):
        mock_driver = MagicMock()
        mock_create_driver.return_value = mock_driver

        # Mock WebDriverWait to just return immediately
        mock_card = MagicMock()
        link_el = MagicMock()
        link_el.text = "Laptop Pro"
        link_el.get_attribute.return_value = "https://amazon.com/laptop"
        price_el = MagicMock()
        price_el.text = "$599.00"
        rating_el = MagicMock()
        rating_el.text = "4.5 out of 5 stars"

        def find_element_dispatch(by, selector):
            if "h2" in selector:
                return link_el
            if "a-offscreen" in selector:
                return price_el
            if "a-icon-alt" in selector:
                return rating_el
            raise Exception("not found")

        mock_card.find_element = MagicMock(side_effect=find_element_dispatch)
        mock_driver.find_elements.return_value = [mock_card]

        with patch("scraper.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = True
            result = scrape_amazon("laptops", 5)

        assert result is not None
        assert len(result) == 1
        assert result[0]["title"] == "Laptop Pro"
        mock_driver.quit.assert_called_once()

    @patch("scraper.create_driver")
    def test_timeout_retries_and_returns_none(self, mock_create_driver):
        mock_driver = MagicMock()
        mock_create_driver.return_value = mock_driver

        with patch("scraper.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.side_effect = TimeoutException("timeout")
            result = scrape_amazon("laptops", 5)

        assert result is None
        assert mock_create_driver.call_count == 2  # 2 retry attempts
        assert mock_driver.quit.call_count == 2

    @patch("scraper.create_driver")
    def test_webdriver_exception_retries(self, mock_create_driver):
        mock_driver = MagicMock()
        mock_create_driver.return_value = mock_driver
        mock_driver.get.side_effect = WebDriverException("browser crashed")

        result = scrape_amazon("laptops")

        assert result is None
        assert mock_create_driver.call_count == 2


# ── scrape_fakestoreapi ──────────────────────────────────────────────────────


class TestScrapeFakeStoreAPI:
    @patch("scraper.requests.get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"title": "Product A", "price": 29.99, "rating": {"rate": 4.1}, "id": 1},
            {"title": "Product B", "price": 9.50, "rating": {"rate": 3.5}, "id": 2},
        ]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = scrape_fakestoreapi(2)
        assert len(result) == 2
        assert result[0]["title"] == "Product A"
        assert result[0]["price"] == "$29.99"
        assert result[1]["rating"] == 3.5

    @patch("scraper.requests.get")
    def test_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_resp

        try:
            scrape_fakestoreapi()
            assert False, "Should have raised HTTPError"
        except requests.HTTPError:
            pass


# ── scrape_products ──────────────────────────────────────────────────────────


class TestScrapeProducts:
    @patch("scraper.scrape_fakestoreapi")
    @patch("scraper.scrape_amazon")
    def test_amazon_succeeds_no_fallback(self, mock_amazon, mock_fakestore, sample_products):
        mock_amazon.return_value = sample_products
        result = scrape_products("laptops", 5)
        assert result == sample_products
        mock_fakestore.assert_not_called()

    @patch("scraper.scrape_fakestoreapi")
    @patch("scraper.scrape_amazon", return_value=None)
    def test_amazon_fails_uses_fallback(self, mock_amazon, mock_fakestore, sample_products):
        mock_fakestore.return_value = sample_products
        result = scrape_products("laptops", 5)
        assert result == sample_products
        mock_amazon.assert_called_once()
        mock_fakestore.assert_called_once()
