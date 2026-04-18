"""
Generate realistic mock data for hackathon demo.
Simulates a BHX store in Ho Chi Minh City.

Run: python -m scripts.generate_mock_data --store-id BHX-HCM001
"""

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.data.skus import SKUS
from app.core.data.recipes import RECIPES

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# Urgency tier → remaining shelf life fraction range
TIER_FRACTIONS = {
    "CRITICAL": (0.00, 0.20),
    "HIGH":     (0.20, 0.40),
    "MEDIUM":   (0.40, 0.70),
    "WATCH":    (0.70, 1.00),
}

# Pantry staples are always in stock at WATCH urgency with high quantity.
# A supermarket never runs out of these — they're restocked constantly.
# ingredient_ids that fall into this category based on shelf life > 30 days
# AND category (sauce, spice, oil, flour, water, noodle dry goods).
_PANTRY_CATEGORIES = {"sauce", "spice", "oil", "flour", "water", "broth"}
_PANTRY_SHELF_LIFE_THRESHOLD = 30  # days


def _is_pantry(sku: dict) -> bool:
    return (
        sku["category_l2"] in _PANTRY_CATEGORIES
        and sku["typical_shelf_life_days"] >= _PANTRY_SHELF_LIFE_THRESHOLD
    )


def generate_batches(store_id: str) -> list:
    """
    Generate batches for all SKUs with no hard cap on total count.

    Strategy:
    - Pantry staples (sauces, spices, oil, flour): always 1 batch at WATCH urgency,
      high unit_count — these are always in stock.
    - Fresh items (meat, seafood, produce): 1–3 stacked batches with realistic
      urgency distribution to give FEFO something to work with.
    - Dry goods / noodles: 1–2 batches at MEDIUM/WATCH.
    """
    today = date.today()
    batches = []
    batch_counter = 0

    # Urgency pool for fresh/perishable items: 10% CRITICAL, 25% HIGH, 45% MEDIUM, 20% WATCH
    fresh_tiers = (
        ["CRITICAL"] * 10 +
        ["HIGH"]     * 25 +
        ["MEDIUM"]   * 45 +
        ["WATCH"]    * 20
    )
    random.shuffle(fresh_tiers)
    tier_idx = 0

    for sku in SKUS:
        shelf_life = sku["typical_shelf_life_days"]

        if _is_pantry(sku):
            # Always in stock: 1 batch, WATCH urgency, large quantity
            lo, hi = TIER_FRACTIONS["WATCH"]
            expiry_days = max(30, round(shelf_life * random.uniform(lo, hi)))
            expiry_date = today + timedelta(days=expiry_days)
            batches.append({
                "batch_id":      f"BATCH-{batch_counter:04d}",
                "store_id":      store_id,
                "sku_id":        sku["sku_id"],
                "ingredient_id": sku["ingredient_id"],
                "product_name":  sku["product_name"],
                "category_l1":   sku["category_l1"],
                "category_l2":   sku["category_l2"],
                "unit_count":    random.randint(5, 10),  # always plenty
                "pack_size_g":   sku["pack_size_g"],
                "retail_price":  sku["retail_price"],
                "cost_price":    sku["cost_price"],
                "created_at":    today.isoformat(),
                "expiry_date":   expiry_date.isoformat(),
                "expiry_days":   expiry_days,
                "urgency_tier":  "WATCH",
            })
            batch_counter += 1

        else:
            # Perishable: 1–3 stacked batches, mixed urgency
            # More stacks → more opportunity for FEFO to demonstrate value
            num_batches = random.randint(1, 3)

            for stack_i in range(num_batches):
                tier = fresh_tiers[tier_idx % len(fresh_tiers)]
                tier_idx += 1

                lo, hi = TIER_FRACTIONS[tier]
                expiry_days = max(1, round(shelf_life * random.uniform(lo, hi)))

                # Stacked batches get slightly different expiry dates
                # to simulate deliveries on different days
                expiry_date = today + timedelta(days=expiry_days + stack_i)

                batches.append({
                    "batch_id":      f"BATCH-{batch_counter:04d}",
                    "store_id":      store_id,
                    "sku_id":        sku["sku_id"],
                    "ingredient_id": sku["ingredient_id"],
                    "product_name":  sku["product_name"],
                    "category_l1":   sku["category_l1"],
                    "category_l2":   sku["category_l2"],
                    "unit_count":    random.randint(2, 8),
                    "pack_size_g":   sku["pack_size_g"],
                    "retail_price":  sku["retail_price"],
                    "cost_price":    sku["cost_price"],
                    "created_at":    today.isoformat(),
                    "expiry_date":   expiry_date.isoformat(),
                    "expiry_days":   expiry_days,
                    "urgency_tier":  tier,
                })
                batch_counter += 1

    return batches


def main():
    parser = argparse.ArgumentParser(description="Generate mock data for hackathon")
    parser.add_argument("--store-id", default="BHX-HCM001", help="Store ID for mock data")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    batches = generate_batches(args.store_id)

    with open(FIXTURES_DIR / "batches.json", "w", encoding="utf-8") as f:
        json.dump(batches, f, ensure_ascii=False, indent=2)

    with open(FIXTURES_DIR / "skus.json", "w", encoding="utf-8") as f:
        json.dump(SKUS, f, ensure_ascii=False, indent=2)

    with open(FIXTURES_DIR / "recipes.json", "w", encoding="utf-8") as f:
        json.dump(RECIPES, f, ensure_ascii=False, indent=2)

    # Summary
    from collections import Counter
    tier_counts = Counter(b["urgency_tier"] for b in batches)
    unique_ings = len({b["ingredient_id"] for b in batches})

    print(f"Generated {len(batches)} batches for store {args.store_id}")
    print(f"  SKUs covered:        {len(SKUS)}")
    print(f"  Recipes exported:    {len(RECIPES)}")
    print(f"  Unique ingredients:  {unique_ings}")
    print(f"  Output:              {FIXTURES_DIR}")
    print(f"  Urgency distribution:")
    for tier in ("CRITICAL", "HIGH", "MEDIUM", "WATCH"):
        print(f"    {tier}: {tier_counts.get(tier, 0)}")


if __name__ == "__main__":
    main()
