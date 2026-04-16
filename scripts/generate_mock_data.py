"""
Generate realistic mock data for hackathon demo.
Simulates a BHX store in Ho Chi Minh City.

Run: python -m scripts.generate_mock_data --store-id BHX-HCM001
"""

import argparse
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.data.skus import SKUS
from app.core.data.recipes import RECIPES

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def generate_batches(store_id: str) -> list:
    """Generate 80 batches with realistic expiry distribution."""
    today = date.today()
    batches = []
    batch_counter = 0

    # Distribution: 10% CRITICAL, 20% HIGH, 40% MEDIUM, 30% WATCH
    expiry_distribution = (
        [1] * 8 +  # 8 batches: CRITICAL (1 day)
        [2] * 8 +
        [3] * 8 +  # 16 batches: HIGH (2-3 days)
        [4, 5, 6, 7] * 10 +  # 40 batches: MEDIUM (4-7 days)
        [14, 21, 30] * 10  # 30 batches: WATCH (14-30 days)
    )[:80]

    random.shuffle(expiry_distribution)

    for sku in SKUS:
        for i in range(random.randint(1, 3)):  # 1-3 batches per SKU
            if batch_counter >= 80:
                break

            expiry_days = expiry_distribution[batch_counter]
            expiry_date = today + timedelta(days=expiry_days)

            batch = {
                "batch_id": f"BATCH-{batch_counter:04d}",
                "store_id": store_id,
                "sku_id": sku["sku_id"],
                "ingredient_id": sku["ingredient_id"],
                "product_name": sku["product_name"],
                "category_l1": sku["category_l1"],
                "category_l2": sku["category_l2"],
                "unit_count": random.randint(2, 8),
                "pack_size_g": sku["pack_size_g"],
                "retail_price": sku["retail_price"],
                "cost_price": sku["cost_price"],
                "created_at": today.isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "expiry_days": expiry_days,
            }
            batches.append(batch)
            batch_counter += 1

        if batch_counter >= 80:
            break

    return batches


def main():
    """Generate mock data and save to fixtures."""
    parser = argparse.ArgumentParser(description="Generate mock data for hackathon")
    parser.add_argument("--store-id", default="BHX-HCM001", help="Store ID for mock data")
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate mock batches
    batches = generate_batches(args.store_id)

    # Save batches
    with open(FIXTURES_DIR / "batches.json", "w", encoding="utf-8") as f:
        json.dump(batches, f, ensure_ascii=False, indent=2)

    # Save SKUs
    with open(FIXTURES_DIR / "skus.json", "w", encoding="utf-8") as f:
        json.dump(SKUS, f, ensure_ascii=False, indent=2)

    # Save recipes
    with open(FIXTURES_DIR / "recipes.json", "w", encoding="utf-8") as f:
        json.dump(RECIPES, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(batches)} batches for store {args.store_id}")
    print(f"  SKUs: {len(SKUS)}")
    print(f"  Recipes: {len(RECIPES)}")
    print(f"  Output: {FIXTURES_DIR}")

    # Print expiry distribution
    critical = sum(1 for b in batches if b["expiry_days"] <= 1)
    high = sum(1 for b in batches if 2 <= b["expiry_days"] <= 3)
    medium = sum(1 for b in batches if 4 <= b["expiry_days"] <= 7)
    watch = sum(1 for b in batches if b["expiry_days"] > 7)
    print(f"  CRITICAL: {critical}, HIGH: {high}, MEDIUM: {medium}, WATCH: {watch}")


if __name__ == "__main__":
    main()
