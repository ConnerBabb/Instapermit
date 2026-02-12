"""
enhancer.py - AI-powered product data enhancement via OpenAI API.

Takes scraped product data and enriches it with:
  1. Category classification (budget / gaming / professional / general)
  2. One-sentence sentiment summary based on rating
  3. Dynamic selector recovery: given a broken CSS selector, asks the LLM
     to suggest a corrected one based on a page HTML snippet.
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
OPENAI_URL = "https://api.openai.com/v1/responses"


def _chat(system: str, user: str, max_tokens: int = 300) -> str:
    """Send a request to the OpenAI Responses API."""
    if not OPENAI_API_KEY:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Export it or pass it in your environment."
        )

    resp = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "input": [
                {"role": "developer", "content": system},
                {"role": "user", "content": user},
            ],
            "max_output_tokens": max_tokens,
            "temperature": 0.3,
            "text": {"format": {"type": "json_object"}},
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    # Extract text from Responses API: output[0].content[0].text
    try:
        content = data["output"][0]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise ValueError(f"Unexpected Responses API shape: {data}")

    return content.strip()


# ── Enhancement 1: Category classification ──────────────────────────────────


def categorize_products(products: list[dict]) -> list[dict]:
    """Add an 'ai_category' field to each product using AI classification."""
    titles = [p["title"] for p in products]

    system = (
        "You are a product classifier. For each product title, assign exactly one "
        "category from: budget, gaming, professional, general. "
        'Respond with a JSON object: {"categories": ["cat1", "cat2", ...]} '
        "one category per title, same order."
    )
    user = json.dumps(titles)

    raw = _chat(system, user)

    try:
        categories = json.loads(raw)["categories"]
    except (json.JSONDecodeError, KeyError):
        categories = ["general"] * len(products)

    for product, cat in zip(products, categories):
        product["ai_category"] = cat

    return products


# ── Enhancement 2: Rating sentiment summary ─────────────────────────────────


def summarize_ratings(products: list[dict]) -> list[dict]:
    """Add an 'ai_sentiment' one-liner based on each product's rating + title."""
    entries = [{"title": p["title"], "rating": p.get("rating")} for p in products]

    system = (
        "For each product, generate a concise one-sentence sentiment summary "
        "based on its rating (out of 5) and title. "
        'Respond with a JSON object: {"sentiments": ["sentence1", "sentence2", ...]} '
        "one per product, same order."
    )
    user = json.dumps(entries)

    raw = _chat(system, user, max_tokens=500)

    try:
        sentiments = json.loads(raw)["sentiments"]
    except (json.JSONDecodeError, KeyError):
        sentiments = ["No sentiment available."] * len(products)

    for product, sent in zip(products, sentiments):
        product["ai_sentiment"] = sent

    return products


# ── Enhancement 3: Dynamic selector recovery ────────────────────────────────


def suggest_selector(failed_selector: str, html_snippet: str, purpose: str = "") -> str:
    """
    Given a CSS selector that no longer matches and a snippet of page HTML,
    ask the LLM to analyze the HTML and find the correct selector.

    Args:
        failed_selector: The CSS selector that returned no matches.
        html_snippet: A chunk of the page HTML for context.
        purpose: What the selector should target (e.g. "product listing cards").
    """
    system = (
        "You are an expert web scraping assistant. "
        "A CSS selector that previously worked no longer matches any elements. "
        "Analyze the provided HTML and find a CSS selector that matches "
        "the target elements described below. "
        'Return a JSON object: {"selector": "<new CSS selector>"}. '
        "No explanation."
    )
    purpose_line = f"Target elements: {purpose}\n" if purpose else ""
    user = (
        f"Previously used selector (no longer works): {failed_selector}\n"
        f"{purpose_line}"
        f"\nPage HTML:\n{html_snippet[:6000]}"
    )
    raw = _chat(system, user, max_tokens=100)

    try:
        return json.loads(raw)["selector"]
    except (json.JSONDecodeError, KeyError):
        return raw


# ── Public API ───────────────────────────────────────────────────────────────


def enhance_products(products: list[dict]) -> list[dict]:
    """
    Run all AI enhancements on the product list.
    Gracefully degrades: if the API key is missing or a call fails,
    the original data is returned with a warning.
    """
    if not OPENAI_API_KEY:
        print("[WARNING] OPENAI_API_KEY not set. Skipping AI enhancements—returning raw data.")
        for p in products:
            p["ai_category"] = "unknown (no API key)"
            p["ai_sentiment"] = "unavailable (no API key)"
        return products

    try:
        products = categorize_products(products)
        print("AI categorization complete.")
    except Exception as exc:
        print(f"[WARNING] Categorization failed: {exc}")

    try:
        products = summarize_ratings(products)
        print("AI sentiment analysis complete.")
    except Exception as exc:
        print(f"[WARNING] Sentiment analysis failed: {exc}")

    return products
