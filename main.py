#!/usr/bin/env python3
"""
main.py - CLI entry point for the product scraper + AI enhancer.

Usage:
    python main.py                        # default: search "laptops"
    python main.py --query="headphones"   # custom search term
    python main.py --query="monitors" --max=10
"""

import argparse
import json

from scraper import scrape_products
from enhancer import enhance_products


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape products from Amazon (or fallback) and enhance with AI."
    )
    parser.add_argument(
        "--query", type=str, default="laptops",
        help="Search keyword (default: laptops)"
    )
    parser.add_argument(
        "--max", type=int, default=5, dest="max_products",
        help="Maximum number of products to scrape (default: 5)"
    )
    args = parser.parse_args()

    # Part 1: Scrape
    products = scrape_products(query=args.query, max_products=args.max_products)

    if not products:
        print("No products found. Exiting.")
        return

    print(f"\n{'='*60}")
    print("RAW SCRAPED DATA")
    print('='*60)
    print(json.dumps(products, indent=2))

    # Part 2: AI Enhancement
    print(f"\n{'='*60}")
    print("ENHANCING WITH AI...")
    print('='*60)
    enhanced = enhance_products(products)

    print(f"\n{'='*60}")
    print("ENHANCED DATA")
    print('='*60)
    print(json.dumps(enhanced, indent=2))


if __name__ == "__main__":
    main()
