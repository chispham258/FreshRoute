"""
P5 — Waste Impact Scoring

INPUT:  List[dict] from P3
OUTPUT: List[dict] with waste_score and waste_score_normalized added
"""

from typing import Dict, List


def compute_waste_score(
    matched_ingredients: List[dict],
    ingredient_status: List[dict],
    sku_lookup: Dict[str, dict],
) -> float:
    """
    Compute waste_score from urgent ingredients only (status == "fulfilled").
    value_rescued = priority_score * cost_per_gram * qty_taken_g
    """
    # Build lookup: ingredient_id -> status entry
    status_by_ing = {s["ingredient_id"]: s for s in ingredient_status}

    waste_score = 0.0
    for matched in matched_ingredients:
        ing_id = matched["ingredient_id"]
        status = status_by_ing.get(ing_id)

        # Only count fulfilled ingredients, not substitutes
        if not status or status["status"] != "fulfilled":
            continue

        priority = matched["priority_score"]

        for batch_used in status["batches_used"]:
            sku = sku_lookup.get(batch_used["sku_id"])
            if not sku:
                continue
            pack_size_g = sku.get("pack_size_g") or 1
            cost_price = sku.get("cost_price", 0)
            cost_per_gram = cost_price / pack_size_g
            value_rescued = priority * cost_per_gram * batch_used["qty_taken_g"]
            waste_score += value_rescued

    return round(waste_score, 4)


def run_p5(
    p3_output: List[dict],
    sku_lookup: Dict[str, dict],
) -> List[dict]:
    """
    Compute waste scores and normalize across batch.

    Args:
        p3_output: validated recipes from P3
        sku_lookup: sku_id -> {cost_price, pack_size_g, ...}
    """
    results = []
    for recipe in p3_output:
        score = compute_waste_score(
            matched_ingredients=recipe["matched_ingredients"],
            ingredient_status=recipe["ingredient_status"],
            sku_lookup=sku_lookup,
        )
        results.append({**recipe, "waste_score": score})

    # Normalize
    max_score = max((r["waste_score"] for r in results), default=1.0)
    if max_score == 0:
        max_score = 1.0

    for r in results:
        r["waste_score_normalized"] = round(r["waste_score"] / max_score, 6)

    return results
