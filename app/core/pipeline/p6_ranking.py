"""
P6 — Multi-objective Ranking

INPUT:  List[dict] from P5 + store weights
OUTPUT: List[dict] top 10 ranked with final_score and rank
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_default_weights() -> dict:
    with open(DATA_DIR / "default_weights.json", encoding="utf-8") as f:
        return json.load(f)


def load_store_weights(store_id: str, firestore_client=None) -> dict:
    """Load weights from Firestore, fall back to cold_start defaults."""
    if firestore_client:
        try:
            doc = firestore_client.collection("stores").document(store_id).get()
            if doc.exists:
                data = doc.to_dict()
                weights = data.get("weights", {})
                if weights:
                    return weights
        except Exception:
            pass

    defaults = load_default_weights()
    return defaults["cold_start"]


def compute_penalty(ingredient_status: List[dict]) -> float:
    """penalty = 0.05 * (n_substitute / n_total) excluding skips."""
    active = [s for s in ingredient_status if s["status"] != "skip"]
    if not active:
        return 0.0
    n_sub = sum(1 for s in active if s["status"] == "substitute")
    return 0.05 * (n_sub / len(active))


def compute_avg_deviation(ingredient_status: List[dict]) -> float:
    """Compute average deviation across fulfilled ingredients."""
    fulfilled = [s for s in ingredient_status if s["status"] in ("fulfilled", "substitute")]
    if not fulfilled:
        return 0.0
    deviations = [s.get("deviation", 0.0) for s in fulfilled]
    return sum(deviations) / len(deviations) if deviations else 0.0


def compute_rounding_loss(ingredient_status: List[dict]) -> float:
    """Compute total rounding loss (over-allocated grams)."""
    total_loss = 0.0
    for status in ingredient_status:
        if status["status"] != "fulfilled":
            continue
        # Rounding loss would be stored if available, otherwise default to 0
        total_loss += status.get("rounding_loss_g", 0.0)
    return total_loss


def compute_final_score(
    recipe: dict,
    weights: dict,
    store_popularity: Optional[Dict[str, float]] = None,
) -> float:
    """
    final_score = w_urgency*urgency + w_complete*completeness + w_waste*waste_norm
                  - w_dev*avg_deviation - w_loss*norm_rounding_loss
                  + w_popularity*popularity - substitute_penalty
    """
    w_urgency = weights.get("w1", 0.40)
    w_complete = weights.get("w2", 0.40)
    w_waste = weights.get("w3", 0.20)
    w_dev = weights.get("w4", 0.10)
    w_loss = weights.get("w5", 0.10)
    w_pop = weights.get("w_popularity", 0.0)

    popularity = 0.0
    if store_popularity and recipe["recipe_id"] in store_popularity:
        popularity = store_popularity[recipe["recipe_id"]]

    avg_dev = recipe.get("avg_deviation", 0.0)
    rounding_loss = recipe.get("total_rounding_loss_g", 0.0)
    # Normalize rounding loss to [0, 1] (assuming max ~1000g loss)
    norm_loss = min(rounding_loss / 1000.0, 1.0)

    penalty = compute_penalty(recipe["ingredient_status"])

    score = (
        w_urgency * recipe["urgency_coverage_score"]
        + w_complete * recipe["completeness_score"]
        + w_waste * recipe["waste_score_normalized"]
        - w_dev * avg_dev
        - w_loss * norm_loss
        + w_pop * popularity
        - penalty
    )
    return round(score, 6)


def run_p6(
    p5_output: List[dict],
    store_id: str,
    firestore_client=None,
    store_popularity: Optional[Dict[str, float]] = None,
    top_k: int = 10,
) -> List[dict]:
    """Rank recipes by final_score, return top K."""
    weights = load_store_weights(store_id, firestore_client)

    results = []
    for recipe in p5_output:
        # Compute packet-based metrics
        avg_dev = compute_avg_deviation(recipe["ingredient_status"])
        rounding_loss = compute_rounding_loss(recipe["ingredient_status"])

        score = compute_final_score(recipe, weights, store_popularity)
        results.append({
            **recipe,
            "final_score": score,
            "avg_deviation": avg_dev,
            "total_rounding_loss_g": rounding_loss,
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    results = results[:top_k]

    # Deduplicate: if two bundles share the same primary ingredient (first
    # required fulfilled/substitute ingredient), keep only the highest-scoring
    # one. Prevents near-identical bundles (e.g. "Cá lóc kho tộ" vs "Cá lóc
    # phi lê kho tộ") from consuming two slots when only one stock pool exists.
    seen_primary: set = set()
    deduped = []
    for r in results:
        primary = next(
            (
                s["ingredient_id"]
                for s in r.get("ingredient_status", [])
                if s["status"] in ("fulfilled", "substitute") and not s.get("is_optional", False)
            ),
            None,
        )
        if primary is None or primary not in seen_primary:
            if primary:
                seen_primary.add(primary)
            deduped.append(r)
    results = deduped

    # Assign ranks
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return results
