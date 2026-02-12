"""
scraper.py - Selenium-based product scraper with fakestoreapi fallback.

Attempts to scrape Amazon search results using Selenium (headless Chrome).
Falls back to fakestoreapi.com/products if Amazon blocks after 2 attempts.
"""

import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


def create_driver() -> webdriver.Chrome:
    """Create a headless Chrome WebDriver with stealth-friendly options."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=opts)


def scrape_amazon(query: str, max_products: int = 5) -> list[dict] | None:
    """
    Attempt to scrape Amazon search results via Selenium.
    Returns a list of product dicts, or None on failure.
    Retries up to 2 times as required by the spec.
    """
    url = f"https://www.amazon.com/s?k={query}"

    for attempt in range(1, 3):  # 2 attempts
        driver = None
        try:
            driver = create_driver()
            driver.get(url)

            # Wait for product cards to appear
            WebDriverWait(driver, 12).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-component-type='s-search-result']")
                )
            )

            cards = driver.find_elements(
                By.CSS_SELECTOR, "[data-component-type='s-search-result']"
            )[:max_products]

            if not cards:
                raise TimeoutException("No product cards found")

            products = []
            for card in cards:
                product = _parse_amazon_card(card)
                if product:
                    products.append(product)

            if products:
                return products

        except (TimeoutException, WebDriverException) as exc:
            print(f"[Attempt {attempt}/2] Amazon scrape failed: {exc}")
        finally:
            if driver:
                driver.quit()

    return None  # Both attempts failed


def _parse_amazon_card(card) -> dict | None:
    """Extract title, price, rating, and URL from a single Amazon result card."""
    try:
        # Title + URL
        link_el = card.find_element(
            By.CSS_SELECTOR,
            "h2 a.a-link-normal"
        )
        title = link_el.text.strip()
        url = link_el.get_attribute("href") or ""

        # Price (may not exist for every listing)
        try:
            price = card.find_element(By.CSS_SELECTOR, "span.a-price > span.a-offscreen").text.strip()
        except Exception:
            price = None

        # Rating
        try:
            rating_text = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt").text
            rating = rating_text.split(" out")[0] if rating_text else None
        except Exception:
            rating = None

        if not title:
            return None

        return {"title": title, "price": price, "rating": rating, "url": url}

    except Exception:
        return None


def scrape_fakestoreapi(max_products: int = 5) -> list[dict]:
    """Fallback: fetch products from fakestoreapi.com via requests."""
    resp = requests.get("https://fakestoreapi.com/products", timeout=10)
    resp.raise_for_status()
    items = resp.json()[:max_products]

    return [
        {
            "title": item["title"],
            "price": f"${item['price']:.2f}",
            "rating": str(item.get("rating", {}).get("rate")),
            "url": f"https://fakestoreapi.com/products/{item['id']}",
        }
        for item in items
    ]


def scrape_products(query: str = "laptops", max_products: int = 5) -> list[dict]:
    """
    Main entry point: try Amazon via Selenium, fall back to fakestoreapi.
    Returns a list of product dicts with title, price, rating, url.
    """
    print(f"Attempting to scrape Amazon for '{query}'...")
    products = scrape_amazon(query, max_products)

    if products:
        print(f"Successfully scraped {len(products)} products from Amazon.")
        return products

    print("Amazon scraping failed after 2 attempts. Falling back to fakestoreapi...")
    products = scrape_fakestoreapi(max_products)
    print(f"Fetched {len(products)} products from fakestoreapi.")
    return products


if __name__ == "__main__":
    results = scrape_products()
    print(json.dumps(results, indent=2))
