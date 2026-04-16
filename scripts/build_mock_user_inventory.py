#!/usr/bin/env python3
"""
Generate realistic mock user home inventories for consumer agent testing.

Produces app/data/mock_user_inventory.json with N users, each having
a randomized subset of ingredients with realistic expiry spreads.

Usage:
    python scripts/build_mock_user_inventory.py [--users N] [--output PATH]
"""

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

# Ingredients a typical Vietnamese home cook might have, with
# typical quantity ranges (grams) and shelf life (days).
HOME_INGREDIENTS = [
    # Proteins
    {"ingredient_id": "thit_heo",      "qty_range": (300, 600),   "shelf_days": (3, 5)},
    {"ingredient_id": "thit_heo_xay",  "qty_range": (200, 400),   "shelf_days": (2, 4)},
    {"ingredient_id": "thit_ga",       "qty_range": (400, 600),   "shelf_days": (3, 5)},
    {"ingredient_id": "thit_bo",       "qty_range": (200, 400),   "shelf_days": (3, 4)},
    {"ingredient_id": "ca_loc",        "qty_range": (300, 500),   "shelf_days": (1, 3)},
    {"ingredient_id": "tom",           "qty_range": (200, 400),   "shelf_days": (1, 3)},
    {"ingredient_id": "muc",           "qty_range": (200, 350),   "shelf_days": (1, 3)},
    {"ingredient_id": "trung_ga",      "qty_range": (300, 600),   "shelf_days": (7, 14)},
    {"ingredient_id": "dau_hu",        "qty_range": (200, 350),   "shelf_days": (3, 5)},
    # Vegetables
    {"ingredient_id": "rau_muong",     "qty_range": (200, 350),   "shelf_days": (1, 3)},
    {"ingredient_id": "cai_xanh",      "qty_range": (200, 350),   "shelf_days": (1, 3)},
    {"ingredient_id": "cai_thia",      "qty_range": (200, 350),   "shelf_days": (1, 3)},
    {"ingredient_id": "ca_chua",       "qty_range": (200, 500),   "shelf_days": (3, 7)},
    {"ingredient_id": "hanh_tay",      "qty_range": (200, 500),   "shelf_days": (7, 14)},
    {"ingredient_id": "ot_chuong",     "qty_range": (150, 300),   "shelf_days": (5, 7)},
    {"ingredient_id": "kho_qua",       "qty_range": (300, 600),   "shelf_days": (3, 5)},
    {"ingredient_id": "bau",           "qty_range": (400, 800),   "shelf_days": (5, 7)},
    # Aromatics & herbs
    {"ingredient_id": "toi",           "qty_range": (100, 200),   "shelf_days": (14, 30)},
    {"ingredient_id": "gung",          "qty_range": (50, 150),    "shelf_days": (7, 21)},
    {"ingredient_id": "hanh_tim",      "qty_range": (100, 200),   "shelf_days": (10, 21)},
    {"ingredient_id": "hanh_la",       "qty_range": (40, 100),    "shelf_days": (1, 3)},
    {"ingredient_id": "sa",            "qty_range": (50, 100),    "shelf_days": (5, 7)},
    {"ingredient_id": "rau_ngo",       "qty_range": (20, 50),     "shelf_days": (1, 3)},
    # Pantry / sauces (long shelf life)
    {"ingredient_id": "nuoc_mam",      "qty_range": (300, 500),   "shelf_days": (90, 365)},
    {"ingredient_id": "xi_dau",        "qty_range": (200, 350),   "shelf_days": (90, 365)},
    {"ingredient_id": "nuoc_dua",      "qty_range": (200, 400),   "shelf_days": (60, 180)},
    {"ingredient_id": "me",            "qty_range": (100, 200),   "shelf_days": (30, 90)},
    # Dairy
    {"ingredient_id": "sua_tuoi",      "qty_range": (500, 1000),  "shelf_days": (5, 10)},
]


def generate_user_inventory(
    user_id: str,
    today: date,
    min_items: int = 6,
    max_items: int = 14,
    urgent_ratio: float = 0.35,
) -> list[dict]:
    """Generate a single user's inventory with realistic expiry distribution."""
    n_items = random.randint(min_items, max_items)
    chosen = random.sample(HOME_INGREDIENTS, min(n_items, len(HOME_INGREDIENTS)))

    inventory = []
    for item in chosen:
        qty = round(random.uniform(*item["qty_range"]), 2)
        shelf_lo, shelf_hi = item["shelf_days"]

        # Force some items to be urgent (expiry_days <= 3)
        if random.random() < urgent_ratio:
            expiry_days = random.randint(0, 3)
        else:
            expiry_days = random.randint(shelf_lo, shelf_hi)

        expiry_date = today + timedelta(days=expiry_days)

        inventory.append({
            "ingredient_id": item["ingredient_id"],
            "quantity_g": qty,
            "expiry_date": expiry_date.isoformat(),
            "expiry_days": expiry_days,
        })

    # Sort by expiry_days so urgent items are first
    inventory.sort(key=lambda x: x["expiry_days"])
    return inventory


def main():
    parser = argparse.ArgumentParser(description="Generate mock user inventories")
    parser.add_argument("--users", type=int, default=5, help="Number of users to generate")
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "app" / "data" / "mock_user_inventory.json"),
        help="Output JSON path",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)
    today = date.today()

    all_users = {}
    for i in range(1, args.users + 1):
        user_id = f"user_{i:03d}"
        all_users[user_id] = generate_user_inventory(user_id, today)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_users, f, ensure_ascii=False, indent=2)

    print(f"Generated inventories for {args.users} users -> {output_path}")
    for uid, inv in all_users.items():
        urgent = sum(1 for item in inv if item["expiry_days"] <= 3)
        print(f"  {uid}: {len(inv)} items ({urgent} urgent)")


if __name__ == "__main__":
    main()
