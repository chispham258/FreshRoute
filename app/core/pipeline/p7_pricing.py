"""
P7 — Dynamic Pricing with Margin Constraint

INPUT:  List[dict] from P6 (top 10 ranked)
OUTPUT: List[BundleOutput] complete bundle objects ready for frontend
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

from app.core.models.bundle import BundleIngredientDisplay, BundleOutput

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_category_margins() -> dict:
    with open(DATA_DIR / "category_margins.json") as f:
        return json.load(f)


def compute_bundle_prices(
    ingredient_status: List[dict],
    sku_lookup: Dict[str, dict],
    p1_ingredient_lookup: Dict[str, str] = None,
) -> dict:
    """
    Compute bundle_retail, bundle_cost, category_costs, and items.
    Only includes fulfilled + substitute (not skip).

    Args:
        ingredient_status: from P3 allocation
        sku_lookup: {sku_id: ProductSKU dict}
        p1_ingredient_lookup: {ingredient_id: urgency_flag} from P1 output
    """
    if p1_ingredient_lookup is None:
        p1_ingredient_lookup = {}

    bundle_retail = 0.0
    bundle_cost = 0.0
    category_costs: Dict[str, float] = {}
    items: List[dict] = []

    for status in ingredient_status:
        if status["status"] in ("skip", "missing"):
            continue

        for batch_used in status["batches_used"]:
            sku_id = batch_used["sku_id"]
            sku = sku_lookup.get(sku_id)
            if not sku:
                continue

            pack_size_g = sku.get("pack_size_g") or 1
            qty = batch_used["qty_taken_g"]

            unit_retail = sku["retail_price"] / pack_size_g
            unit_cost = sku["cost_price"] / pack_size_g
            item_retail = unit_retail * qty
            item_cost = unit_cost * qty

            bundle_retail += item_retail
            bundle_cost += item_cost

            cat = sku.get("category_l1", "processed")
            category_costs[cat] = category_costs.get(cat, 0) + item_cost

            # Look up urgency_flag from P1 output via ingredient_id
            ingredient_id = status["ingredient_id"]
            urgency_flag = p1_ingredient_lookup.get(ingredient_id)

            items.append({
                "ingredient_id": ingredient_id,
                "sku_id": sku_id,
                "product_name": sku.get("product_name", ""),
                "qty_taken_g": qty,
                "item_retail_price": round(item_retail, 2),
                "is_substitute": status["status"] == "substitute",
                "substitute_id": status.get("substitute_id"),
                "urgency_flag": urgency_flag,
            })

    return {
        "bundle_retail": round(bundle_retail, 2),
        "bundle_cost": round(bundle_cost, 2),
        "category_costs": category_costs,
        "items": items,
    }


def compute_weighted_min_margin(
    category_costs: Dict[str, float],
    bundle_cost: float,
    category_margins: Dict[str, float],
) -> float:
    """Weighted min_margin based on cost proportion per category."""
    if bundle_cost == 0:
        return 0.12
    margin = 0.0
    for cat, cost in category_costs.items():
        weight = cost / bundle_cost
        cat_margin = category_margins.get(cat, 0.15)
        margin += weight * cat_margin
    return round(margin, 6)


def apply_discount(
    bundle_retail: float,
    bundle_cost: float,
    waste_score_normalized: float,
    min_margin: float,
) -> dict:
    """Apply discount with margin floor constraint."""
    if bundle_retail == 0:
        return {
            "discount_rate": 0.0,
            "final_price": 0.0,
            "gross_profit": 0.0,
            "gross_margin": 0.0,
        }

    raw_discount = min(0.05 + 0.25 * waste_score_normalized, 0.30)
    discounted_price = bundle_retail * (1 - raw_discount)

    achieved_margin = (discounted_price - bundle_cost) / discounted_price if discounted_price > 0 else 0

    if achieved_margin >= min_margin:
        final_price = discounted_price
        actual_discount = raw_discount
    else:
        # Fall back to min_margin-safe price
        final_price = bundle_cost / (1 - min_margin) if min_margin < 1 else bundle_cost
        actual_discount = 1 - (final_price / bundle_retail) if bundle_retail > 0 else 0

    gross_profit = final_price - bundle_cost
    gross_margin = gross_profit / final_price if final_price > 0 else 0

    return {
        "discount_rate": round(max(actual_discount, 0), 4),
        "final_price": round(final_price, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin": round(gross_margin, 6),
    }


def run_p7(
    p6_output: List[dict],
    sku_lookup: Dict[str, dict],
    recipe_names: Dict[str, str],
    store_id: str,
    category_margins: Dict[str, float] = None,
    p1_ingredient_lookup: Dict[str, str] = None,
) -> List[BundleOutput]:
    """Build final BundleOutput objects with pricing.

    Args:
        p6_output: ranked recipes from P6
        sku_lookup: {sku_id: ProductSKU dict}
        recipe_names: {recipe_id: name}
        store_id: store identifier
        category_margins: category-specific profit margins
        p1_ingredient_lookup: {ingredient_id: urgency_flag} from P1 for enrichment
    """
    if category_margins is None:
        category_margins = _load_category_margins()

    if p1_ingredient_lookup is None:
        p1_ingredient_lookup = {}

    today_str = date.today().strftime("%Y%m%d")
    now = datetime.now()
    bundles = []

    for recipe in p6_output:
        recipe_id = recipe["recipe_id"]
        bundle_id = f"{recipe_id}__{store_id}__{today_str}"

        prices = compute_bundle_prices(recipe["ingredient_status"], sku_lookup, p1_ingredient_lookup)
        min_margin = compute_weighted_min_margin(
            prices["category_costs"],
            prices["bundle_cost"],
            category_margins,
        )
        discount = apply_discount(
            prices["bundle_retail"],
            prices["bundle_cost"],
            recipe.get("waste_score_normalized", 0),
            min_margin,
        )

        display_ingredients = [
            BundleIngredientDisplay(**item) for item in prices["items"]
        ]

        bundles.append(BundleOutput(
            bundle_id=bundle_id,
            recipe_id=recipe_id,
            recipe_name=recipe_names.get(recipe_id, recipe_id),
            rank=recipe["rank"],
            final_score=recipe["final_score"],
            urgency_coverage_score=recipe["urgency_coverage_score"],
            completeness_score=recipe["completeness_score"],
            waste_score_normalized=recipe.get("waste_score_normalized", 0),
            original_price=prices["bundle_retail"],
            discount_rate=discount["discount_rate"],
            final_price=discount["final_price"],
            gross_profit=discount["gross_profit"],
            gross_margin=discount["gross_margin"],
            ingredients=display_ingredients,
            has_substitute=any(i.is_substitute for i in display_ingredients),
            store_id=store_id,
            generated_at=now,
        ))

    return bundles
