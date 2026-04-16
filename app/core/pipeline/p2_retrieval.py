"""
P2 — Recipe Retrieval via Inverted Index

INPUT:  List[P1Output] from P1
OUTPUT: List[dict] top 20 recipe candidates with urgency_coverage_score
"""

from collections import defaultdict
from typing import Dict, List

from app.core.models.inventory import P1Output


def build_urgent_set(p1_output: List[P1Output]) -> Dict[str, List[P1Output]]:
    """Group P1 batches by ingredient_id. Keep each batch separate."""
    urgent = defaultdict(list)
    for batch in p1_output:
        urgent[batch.ingredient_id].append(batch)
    return dict(urgent)


def load_inverted_index_from_recipes(recipes: List[dict]) -> Dict[str, List[str]]:
    """
    Build ingredient_id -> [recipe_ids] from recipe list.
    Used when loading from fixture data instead of DB.
    """
    index = defaultdict(list)
    for recipe in recipes:
        for ing in recipe.get("ingredients", []):
            index[ing["ingredient_id"]].append(recipe["recipe_id"])
    return dict(index)


def compute_urgency_coverage_score(
    matched_ingredient_ids: List[str],
    urgent_set: Dict[str, List[P1Output]],
) -> float:
    """
    Score = max_priority + 0.3 * sum(remaining priorities).
    Each ingredient_id contributes its max batch priority.
    """
    priorities = []
    for ing_id in matched_ingredient_ids:
        batches = urgent_set.get(ing_id, [])
        if batches:
            max_priority = max(b.priority_score for b in batches)
            priorities.append(max_priority)

    if not priorities:
        return 0.0

    priorities.sort(reverse=True)
    score = priorities[0] + 0.3 * sum(priorities[1:])
    return round(score, 6)


def run_p2(
    p1_output: List[P1Output],
    ingredient_to_recipes: Dict[str, List[str]],
    recipe_lookup: Dict[str, dict],
    top_k: int = 20,
) -> List[dict]:
    """
    Retrieve top-K recipe candidates based on urgent ingredient overlap.

    Args:
        p1_output: priority-scored batches from P1
        ingredient_to_recipes: inverted index (ingredient_id -> [recipe_ids])
        recipe_lookup: recipe_id -> recipe dict
        top_k: number of candidates to return
    """
    urgent_set = build_urgent_set(p1_output)

    # Find candidate recipes and which urgent ingredients they match
    candidates: Dict[str, set] = defaultdict(set)
    for ing_id in urgent_set:
        recipe_ids = ingredient_to_recipes.get(ing_id, [])
        for rid in recipe_ids:
            candidates[rid].add(ing_id)

    # Score each candidate
    results = []
    for recipe_id, matched_ids in candidates.items():
        matched_list = list(matched_ids)
        score = compute_urgency_coverage_score(matched_list, urgent_set)

        # Build matched_ingredients detail
        matched_ingredients = []
        for ing_id in matched_list:
            batches = urgent_set[ing_id]
            best = max(batches, key=lambda b: b.priority_score)
            matched_ingredients.append({
                "ingredient_id": ing_id,
                "priority_score": best.priority_score,
                "batch_id": best.batch_id,
                "remaining_qty_g": best.remaining_qty_g,
                "urgency_flag": best.urgency_flag,
            })

        results.append({
            "recipe_id": recipe_id,
            "urgency_coverage_score": score,
            "n_matched": len(matched_list),
            "matched_ingredients": sorted(
                matched_ingredients,
                key=lambda x: x["priority_score"],
                reverse=True,
            ),
        })

    # Sort by score descending, return top K
    results.sort(key=lambda x: x["urgency_coverage_score"], reverse=True)
    return results[:top_k]
