# Product Scraper + AI Enhancer

Selenium-based Amazon product scraper with AI-powered data enrichment.

## Setup

```bash
pip install -r requirements.txt
```

Chrome and ChromeDriver must be installed and on your PATH.

Set your OpenAI API key for Part 2 enhancements:

```bash
export OPENAI_API_KEY="sk-..."
```

## Usage

```bash
# Default: scrape 5 laptop listings
python main.py

# Custom search
python main.py --query="headphones"

# Custom search + max results
python main.py --query="monitors" --max=10
```

## Architecture

| File          | Purpose                                            |
|---------------|----------------------------------------------------|
| `main.py`     | CLI entry point, orchestrates scrape + enhance      |
| `scraper.py`  | Selenium Amazon scraper + fakestoreapi fallback     |
| `enhancer.py` | OpenAI-powered categorization, sentiment, selectors |

## How it works

### Part 1 — Scraping
1. Launches headless Chrome and searches Amazon for the given query.
2. Uses `WebDriverWait` (explicit waits) — no `time.sleep()` calls.
3. Extracts **title, price, rating, URL** from each product card.
4. If Amazon blocks both attempts, falls back to `fakestoreapi.com/products`.

### Part 2 — AI Enhancement
With a valid `OPENAI_API_KEY`, the enhancer adds two fields to each product:

- **`ai_category`** — classifies the product as `budget`, `gaming`, `professional`, or `general`.
- **`ai_sentiment`** — a one-sentence sentiment summary based on the rating.

A third utility, `suggest_selector()`, demonstrates dynamic selector recovery:
given a broken CSS/XPath selector and an HTML snippet, the LLM returns a corrected selector.

If no API key is set the script still runs — enhancements are skipped gracefully.
