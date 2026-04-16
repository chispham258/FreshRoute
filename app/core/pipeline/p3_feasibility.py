"""
P3 — Feasibility Validation

INPUT:  List[dict] from P2 + full store inventory + substitute_groups
OUTPUT: List[dict] valid recipes only, with completeness_score and ingredient_status
"""

from collections import defaultdict
from typing import Dict, List, Optional

from app.core.engine.allocation import allocate_fefo


def build_ingredient_batches(full_inventory: List[dict]) -> Dict[str, List[dict]]:
    """Group ALL store batches by ingredient_id, sort by expiry_days ASC (FEFO)."""
    grouped = defaultdict(list)
    for batch in full_inventory:
        # Ensure batch has quantity info
        qty = batch.get("remaining_qty_g", 0)
        if qty <= 0:
            # Try to compute from packet-based fields
            if "unit_count" in batch and "pack_size_g" in batch:
                qty = batch["unit_count"] * batch["pack_size_g"]
            else:
                continue

        if qty > 0:
            grouped[batch["ingredient_id"]].append(batch)

    # Sort each group FEFO (nearest expiry first)
    for ing_id in grouped:
        grouped[ing_id].sort(key=lambda b: b.get("expiry_days", 999))

    return dict(grouped)


def check_ingredient(
    ingredient_id: str,
    required_qty_g: float,
    is_optional: bool,
    ingredient_batches: Dict[str, List[dict]],
    substitute_groups: Dict[str, List[str]],
) -> dict:
    """
    Check if an ingredient can be fulfilled using packet-based allocation.
    Tries primary ingredient, then substitutes, with FEFO ordering.
    """
    def _try_allocation(ing_id: str) -> dict:
        """Try to allocate using best strategy."""
        batches = ingredient_batches.get(ing_id, [])
        if not batches:
            return None

        result = allocate_fefo(batches, required_qty_g, strategy="best")
        if result.feasible:
            return {
                "allocated_g": result.allocated_g,
                "deviation": result.deviation,
                "strategy": result.strategy,
                "batches_used": result.batches_used,
            }
        return None

    # Try primary ingredient
    alloc = _try_allocation(ingredient_id)
    if alloc:
        return {
            "ingredient_id": ingredient_id,
            "status": "fulfilled",
            "is_optional": is_optional,
            "substitute_id": None,
            "allocated_g": alloc["allocated_g"],
            "deviation": alloc["deviation"],
            "allocation_strategy": alloc["strategy"],
            "batches_used": [
                {
                    "batch_id": b["batch_id"],
                    "sku_id": b["sku_id"],
                    "qty_taken_g": b["grams_taken"],
                }
                for b in alloc["batches_used"]
            ],
        }

    # Try substitutes
    substitutes = substitute_groups.get(ingredient_id, [])
    for sub_id in substitutes:
        alloc = _try_allocation(sub_id)
        if alloc:
            return {
                "ingredient_id": ingredient_id,
                "status": "substitute",
                "is_optional": is_optional,
                "substitute_id": sub_id,
                "allocated_g": alloc["allocated_g"],
                "deviation": alloc["deviation"],
                "allocation_strategy": alloc["strategy"],
                "batches_used": [
                    {
                        "batch_id": b["batch_id"],
                        "sku_id": b["sku_id"],
                        "qty_taken_g": b["grams_taken"],
                    }
                    for b in alloc["batches_used"]
                ],
            }

    # Not available
    if is_optional:
        return {
            "ingredient_id": ingredient_id,
            "status": "skip",
            "is_optional": True,
            "substitute_id": None,
            "allocated_g": 0.0,
            "deviation": 0.0,
            "allocation_strategy": "none",
            "batches_used": [],
        }

    return {
        "ingredient_id": ingredient_id,
        "status": "missing",
        "is_optional": False,
        "substitute_id": None,
        "allocated_g": 0.0,
        "deviation": 0.0,
        "allocation_strategy": "none",
        "batches_used": [],
    }


def _compute_completeness(ingredient_status: List[dict]) -> float:
    """
    completeness = req_fulfilled/total_required + 0.3 * opt_fulfilled/total_optional
    """
    required = [s for s in ingredient_status if not s["is_optional"]]
    optional = [s for s in ingredient_status if s["is_optional"]]

    req_fulfilled = sum(1 for s in required if s["status"] in ("fulfilled", "substitute"))
    total_required = len(required)

    opt_fulfilled = sum(1 for s in optional if s["status"] in ("fulfilled", "substitute"))
    total_optional = len(optional)

    score = 0.0
    if total_required > 0:
        score += req_fulfilled / total_required
    if total_optional > 0:
        score += 0.3 * (opt_fulfilled / total_optional)

    return round(score, 6)


def run_p3(
    p2_output: List[dict],
    recipe_requirements: Dict[str, List[dict]],
    full_inventory: List[dict],
    substitute_groups: Dict[str, List[str]],
) -> List[dict]:
    """
    Validate feasibility for each recipe candidate using packet-based allocation.

    Args:
        p2_output: candidates from P2
        recipe_requirements: recipe_id -> List[{ingredient_id, required_qty_g, is_optional, role}]
        full_inventory: ALL batches in store (not just P1 top-N)
        substitute_groups: ingredient_id -> List[substitute_ids]

    Returns: valid recipes with completeness_score and ingredient_status added
    """
    ingredient_batches = build_ingredient_batches(full_inventory)
    valid = []

    for candidate in p2_output:
        recipe_id = candidate["recipe_id"]
        requirements = recipe_requirements.get(recipe_id, [])

        if not requirements:
            continue

        ingredient_status = []
        has_missing = False

        for req in requirements:
            status = check_ingredient(
                ingredient_id=req["ingredient_id"],
                required_qty_g=req["required_qty_g"],
                is_optional=req.get("is_optional", False),
                ingredient_batches=ingredient_batches,
                substitute_groups=substitute_groups,
            )
            if status["status"] == "missing":
                has_missing = True
                break
            ingredient_status.append(status)

        if has_missing:
            continue

        completeness_score = _compute_completeness(ingredient_status)

        valid.append({
            **candidate,
            "completeness_score": completeness_score,
            "ingredient_status": ingredient_status,
        })

    return valid
