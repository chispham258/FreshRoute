"""
Agent tools for LangGraph ReAct loop (clean, test-focused subset).

This file implements the tools required by the test-suite in a clear,
well-typed manner: name resolution, urgent inventory fetching, recipe
search, and feasibility / substitution checks using packet-based allocation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Dict

from app.agent.shared.ontology import query_ontology
from app.integrations.connectors.mock import MockConnector
from app.core.engine.allocation import allocate_fefo
from app.core.data.repository import DataRepository

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures"

connector = MockConnector()


# ============================================================================
# Name resolution
# ============================================================================
def resolve_ingredient_name(user_input: str) -> Optional[str]:
    """Resolve a user's ingredient name to ingredient_id."""
    text = user_input.strip().lower()
    if not text:
        return None
    aliases = DataRepository.get().ingredient_aliases()
    # exact match
    if text in aliases:
        return aliases[text]
    # substring matches
    candidates = [(a, i) for a, i in aliases.items() if text in a or a in text]
    if not candidates:
        return None
    candidates.sort(key=lambda x: len(x[0]))
    return candidates[0][1]


def resolve_ingredient_names(user_inputs: List[str]) -> List[dict]:
    """Resolve a list of user ingredient names to ingredient_ids."""
    results = []
    for ui in user_inputs:
        ing_id = resolve_ingredient_name(ui)
        results.append({
            "input": ui,
            "ingredient_id": ing_id,
            "resolved": ing_id is not None,
        })
    return results


# ============================================================================
# Urgent inventory (P1 scoring)
# ============================================================================
def get_urgent_inventory(store_id: str, top_n: int = 20) -> List[dict]:
    """Fetch top N urgent (near-expiry) batches for a store via P1 scoring.
    
    Uses cached P1 scores if available, otherwise runs P1 and caches result.
    Tests that use synthetic store_ids will still get results because 
    MockConnector returns all fixtures when a store doesn't exist.
    """
    from app.core.pipeline.p1_priority import run_p1
    from app.core.pipeline import p1_cache

    # Check cache first
    cached = p1_cache.get(store_id)
    if cached:
        top = sorted(cached, key=lambda x: x.priority_score, reverse=True)[:top_n]
        return [_p1_output_to_dict(o) for o in top]

    # Cache miss: run P1 from scratch
    repo = DataRepository.get()
    batches_raw = connector.get_batches(store_id)
    batches = []
    for b in batches_raw:
        if hasattr(b, "model_dump"):
            d = b.model_dump()
        elif hasattr(b, "dict"):
            d = b.dict()
        elif isinstance(b, dict):
            d = b
        else:
            d = dict(b)
        if "remaining_qty_g" not in d:
            d["remaining_qty_g"] = d.get("unit_count", 1) * d.get("pack_size_g", 500)
        batches.append(d)

    all_sku_ids = {b.get("sku_id") for b in batches if b.get("sku_id")}
    sales_history = {sku_id: connector.get_sales_history(store_id, sku_id) for sku_id in all_sku_ids}

    p1_scores = run_p1(batches, sales_history, repo.sku_lookup(), top_n=len(batches))
    p1_cache.put(store_id, p1_scores)

    top = sorted(p1_scores, key=lambda x: x.priority_score, reverse=True)[:top_n]
    return [_p1_output_to_dict(o) for o in top]


def _p1_output_to_dict(p1_output) -> dict:
    """Convert P1Output namedtuple to dict for JSON serialization."""
    return {
        "batch_id": p1_output.batch_id,
        "ingredient_id": p1_output.ingredient_id,
        "sku_id": p1_output.sku_id,
        "expiry_days": p1_output.expiry_days,
        "remaining_qty_g": p1_output.remaining_qty_g,
        "priority_score": round(p1_output.priority_score, 4),
        "urgency_flag": p1_output.urgency_flag,
    }


# ============================================================================
# Recipe search
# ============================================================================
def search_recipes_from_ingredients(
    ingredient_ids: List[str],
    ingredient_urgency: Optional[Dict[str, float]] = None,
    top_k: int = 10,
) -> List[dict]:
    """Find recipes that best cover a set of urgent ingredients.
    
    Scores recipes by max urgency + 0.3 × sum(other urgencies) if ingredient_urgency
    is provided, otherwise by simple ingredient count.
    """
    with open(FIXTURES_DIR / "mock_recipes.json", encoding="utf-8") as f:
        recipes = json.load(f)

    scored = []
    for recipe in recipes:
        recipe_ings = {ing["ingredient_id"] for ing in recipe.get("ingredients", [])}
        matched = list(set(ingredient_ids) & recipe_ings)
        if not matched:
            continue

        if ingredient_urgency:
            priorities = sorted([ingredient_urgency.get(i, 0.0) for i in matched], reverse=True)
            urgency_score = round(priorities[0] + 0.3 * sum(priorities[1:]), 6)
        else:
            urgency_score = float(len(matched))

        scored.append({
            "recipe_id": recipe["recipe_id"],
            "name": recipe.get("name", ""),
            "matched_count": len(matched),
            "urgency_score": urgency_score,
            "ingredients": recipe.get("ingredients", []),
        })

    scored.sort(key=lambda x: x["urgency_score"], reverse=True)
    return scored[:top_k]


# ============================================================================
# Feasibility & substitution (packet-based FEFO allocation)
# ============================================================================
def check_feasibility_and_substitute(
    recipe: dict,
    store_id_or_inventory: str | list = "BHX-HCM001",
) -> dict:
    """Check recipe feasibility using packet-based FEFO allocation + ontology substitutes.
    
    Args:
        recipe: dict with "ingredients" list of {ingredient_id, required_qty_g}
        store_id_or_inventory: either a store_id string (fetches via connector) or
                               an explicit inventory list (used by tests)
    
    Returns:
        dict with "ingredient_status", "completeness_score", "feasible" fields
    """
    # Accept explicit inventory list (for tests) or look up via store_id
    if isinstance(store_id_or_inventory, (list, tuple)):
        full_inventory = store_id_or_inventory
    else:
        full_inventory = connector.get_batches(store_id_or_inventory)

    # Convert Pydantic models to dicts
    inventory_dicts = []
    for b in full_inventory:
        if hasattr(b, "model_dump"):
            inventory_dicts.append(b.model_dump())
        elif hasattr(b, "dict"):
            inventory_dicts.append(b.dict())
        elif isinstance(b, dict):
            inventory_dicts.append(b)
        else:
            inventory_dicts.append(dict(b))

    ingredient_status = []
    for req in recipe.get("ingredients", []):
        ing_id = req["ingredient_id"]
        needed = req["required_qty_g"]

        # Find batches of this ingredient
        batches = [b for b in inventory_dicts if b.get("ingredient_id") == ing_id]
        chosen_sub = None
        allocation = None
        status = "missing"

        if batches:
            # Try primary ingredient
            allocation = allocate_fefo(batches, required_g=needed, strategy="best")
            if allocation.feasible:
                status = "fulfilled"
            else:
                # Primary allocation failed; try substitutes (keep allocation for metrics)
                subs = query_ontology(ing_id, relation="substitute")
                for sub_id in subs.get("substitutes", []):
                    sub_batches = [b for b in inventory_dicts if b.get("ingredient_id") == sub_id]
                    if not sub_batches:
                        continue
                    sub_alloc = allocate_fefo(sub_batches, required_g=needed, strategy="best")
                    if sub_alloc.feasible:
                        status = "substitute"
                        chosen_sub = sub_id
                        allocation = sub_alloc
                        break
        else:
            # No primary batches; try substitutes
            subs = query_ontology(ing_id, relation="substitute")
            for sub_id in subs.get("substitutes", []):
                sub_batches = [b for b in inventory_dicts if b.get("ingredient_id") == sub_id]
                if not sub_batches:
                    continue
                sub_alloc = allocate_fefo(sub_batches, required_g=needed, strategy="best")
                if sub_alloc.feasible:
                    status = "substitute"
                    chosen_sub = sub_id
                    allocation = sub_alloc
                    break

        # Populate allocation metrics (even if allocation is infeasible, preserve metrics)
        if allocation is not None:
            allocated_g = allocation.allocated_g
            deviation = allocation.deviation
            allocation_strategy = allocation.strategy
            batches_used = [
                {
                    "sku_id": b.get("sku_id", ""),
                    "batch_id": b["batch_id"],
                    "qty_taken_g": b["grams_taken"],
                }
                for b in allocation.batches_used
            ]
        else:
            allocated_g = 0.0
            deviation = 1.0
            allocation_strategy = "none"
            batches_used = []

        ingredient_status.append({
            "ingredient_id": ing_id,
            "status": status,
            "substitute_id": chosen_sub,
            "required_qty_g": needed,
            "allocated_g": allocated_g,
            "deviation": deviation,
            "allocation_strategy": allocation_strategy,
            "batches_used": batches_used,
        })

    # Compute completeness score
    total = len(ingredient_status)
    fulfilled_count = sum(1 for s in ingredient_status if s["status"] in ("fulfilled", "substitute"))
    completeness = fulfilled_count / total if total > 0 else 0.0

    return {
        "recipe": recipe,
        "ingredient_status": ingredient_status,
        "completeness_score": round(completeness, 3),
        "feasible": completeness >= 0.7,
    }


# ============================================================================
# Minimal consumer-facing tools (stubs for now)
# ============================================================================
def note_allergy(allergy_names: List[str]) -> dict:
    """Record allergens for the conversation session (tool-as-memory pattern)."""
    resolved = resolve_ingredient_names(allergy_names)
    ids = [r["ingredient_id"] for r in resolved if r["resolved"]]
    unresolved = [r["input"] for r in resolved if not r["resolved"]]
    return {
        "allergy_ids": ids,
        "unresolved": unresolved,
        "note": "Allergens recorded. Always pass allergy_ids to find_recipes_for_consumer.",
    }


def get_ingredient_display_name(ingredient_id: str) -> str:
    """Get human-readable Vietnamese name for an ingredient_id."""
    repo = DataRepository.get()
    aliases = repo.ingredient_aliases()
    id_to_display = {}
    for alias, ing_id in aliases.items():
        if ing_id not in id_to_display:
            id_to_display[ing_id] = alias
    return id_to_display.get(ingredient_id, ingredient_id.replace("_", " "))
