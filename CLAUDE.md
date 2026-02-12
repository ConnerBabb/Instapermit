# Instapermit

## Project overview

Python CLI tool that scrapes product listings from Amazon (Selenium) with a fakestoreapi.com fallback, then enriches them with OpenAI-powered AI enhancements (categorization, sentiment, selector recovery).

## Tech stack

- Python 3.13, no packaging — run directly with `python main.py`
- Selenium + webdriver-manager for browser automation
- Raw `requests.post` to OpenAI API (not the openai SDK)
- pytest for testing, ruff for linting/formatting

## Code style

- Type hints on all function signatures
- Line length: 100 chars
- Ruff rules: E, F, W, I (isort)
- Double quotes for strings
- Third-party imports separated from stdlib by a blank line

## Commands

```bash
# Run the tool
python main.py --query="laptops" --max=5

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Lint
ruff check .

# Format check
ruff format --check .

# Auto-fix lint + format
ruff check --fix . && ruff format .
```

## Testing conventions

- All tests live in `tests/`
- Selenium is fully mocked — tests never launch a real browser
- OpenAI API is fully mocked — tests never make real API calls
- Patch `enhancer.OPENAI_API_KEY` directly (module-level variable set at import time)
- Use `copy.deepcopy(sample_products)` when tests mutate fixture data
- Shared fixtures in `tests/conftest.py`: `sample_products`, `mock_openai_response`

## Architecture decisions

- `scraper.py`: `scrape_amazon()` retries 2x, then `scrape_products()` falls back to `scrape_fakestoreapi()`
- `enhancer.py`: `enhance_products()` gracefully degrades — if no API key, returns products with placeholder fields; if one enhancement fails, the other still runs
- `_chat()` raises `EnvironmentError` when `OPENAI_API_KEY` is empty

## Git workflow

- Default branch: `master`
- Branch protection requires `lint` and `test` CI checks to pass on PRs
- Squash merge preferred (merge commits disabled)
- Branches auto-delete on merge
- Branch naming: `feature/`, `bugfix/`, `hotfix/`

## PR workflow

**Every PR must go through this process — no exceptions:**

1. Run `ruff check .` and `ruff format --check .` — fix any issues before proceeding
2. Run `pytest` — all tests must pass locally
3. Run `/security-review` to perform a full security review of all pending changes
4. Only after security review passes, create the PR with `gh pr create`
5. After PR creation, watch for CI checks to complete: `gh pr checks --watch`
6. If any checks fail, fix the issues, push, and re-watch

Use the `/secure-pr` skill to automate this entire flow.

## Security

- Never commit `.env` files or API keys
- `OPENAI_API_KEY` must be set via environment variable, never hardcoded
- Secret scanning with push protection is enabled on the repo
- CodeQL runs on every push/PR and weekly for security analysis
- Dependabot monitors dependencies for vulnerabilities
