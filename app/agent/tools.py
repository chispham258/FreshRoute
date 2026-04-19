"""
Agent tools for LangGraph ReAct loop.

B2B tools (existing):
  - get_urgent_inventory: fetch near-expiry batches for a store
  - search_recipes_from_ingredients: find recipes matching ingredient list
  - check_feasibility_and_substitute: P3-style feasibility + ontology substitution
  - calculate_pricing_and_waste: P7-style pricing (placeholder)

Consumer tools - Discovery Mode (Phase 2):
  - resolve_ingredient_names: map Vietnamese names to ingredient IDs
  - get_user_inventory: load a consumer's home inventory
  - get_user_urgent_ingredients: filter user inventory to near-expiry items
  - find_recipes_for_consumer: score recipes prioritizing urgent ingredients
  - adjust_recipe_for_user: substitute allergens and unavailable ingredients

Consumer tools - Shopping Mode (Phase 2.1):
  - get_recipe_by_name: find recipe by Vietnamese name (fuzzy match)
  - get_remaining_ingredients: compute shopping list for a recipe
  - get_ingredient_suggestions: smart substitutes and alternatives

Shared:
  - query_ontology: ontology lookup for substitutes
"""

import json
from pathlib import Path
from typing import List, Optional

from app.agent.shared.ontology import query_ontology
from app.integrations.connectors.mock import MockConnector
from app.core.models.bundle import BundleOutput
from app.core.engine.allocation import allocate_fefo, MAX_DEVIATION

# Project root is 2 levels up from app/agent/tools.py (→ app → FreshRoute)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures"
DATA_DIR = _PROJECT_ROOT / "app" / "core" / "data"

connector = MockConnector()


# ---------------------------------------------------------------------------
# Ingredient name ↔ ID resolution (moved to DataRepository)
# ---------------------------------------------------------------------------

from app.core.data.repository import DataRepository


def resolve_ingredient_name(user_input: str) -> Optional[str]:
    """
    Resolve a user's natural-language ingredient name to an ingredient_id.

    Tries exact match first, then case-insensitive, then substring match.
    Returns None if no match found — the agent should ask the user to clarify.
    """
    text = user_input.strip().lower()

    if not text:
        return None

    aliases = DataRepository.get().ingredient_aliases()

    # Exact match
    if text in aliases:
        return aliases[text]

    # Substring match (user typed partial name)
    candidates = [
        (alias, ing_id)
        for alias, ing_id in aliases.items()
        if text in alias or alias in text
    ]
    if len(candidates) == 1:
        return candidates[0][1]

    # Multiple matches — return the shortest alias match (most specific)
    if candidates:
        candidates.sort(key=lambda x: len(x[0]))
        return candidates[0][1]

    return None


def resolve_ingredient_names(user_inputs: List[str]) -> List[dict]:
    """
    Resolve a list of user ingredient names to ingredient_ids.

    Returns list of {input, ingredient_id, resolved} dicts.
    Unresolved items have ingredient_id=None so the agent can ask for clarification.
    """
    results = []
    for name in user_inputs:
        ing_id = resolve_ingredient_name(name)
        results.append({
            "input": name,
            "ingredient_id": ing_id,
            "resolved": ing_id is not None,
        })
    return results


def note_allergy(allergy_names: List[str]) -> dict:
    """
    Record allergens for the current conversation session.

    Resolves Vietnamese ingredient names to system IDs and stores them as
    a structured result in the conversation history. The LLM should call
    this IMMEDIATELY whenever the user mentions food allergies or intolerances.
    Subsequent calls to find_recipes_for_consumer and adjust_recipe_for_user
    MUST pass the allergy_ids returned here.

    Args:
        allergy_names: Vietnamese names the user cannot eat (e.g. ["trứng", "hải sản"]).

    Returns:
        {"allergy_ids": [...], "note": "..."} — pass allergy_ids to find_recipes_for_consumer.
    """
    resolved = resolve_ingredient_names(allergy_names)
    ids = [r["ingredient_id"] for r in resolved if r["resolved"]]
    unresolved = [r["input"] for r in resolved if not r["resolved"]]
    return {
        "allergy_ids": ids,
        "unresolved": unresolved,
        "note": (
            f"Allergens recorded: {ids}. "
            "Always pass these IDs as the allergies parameter to "
            "find_recipes_for_consumer and adjust_recipe_for_user."
        ),
    }


def get_ingredient_display_name(ingredient_id: str) -> str:
    """Get a human-readable Vietnamese name for an ingredient_id."""
    repo = DataRepository.get()
    aliases = repo.ingredient_aliases()

    # Build reverse map: ingredient_id → display name (first alias)
    id_to_display = {}
    for alias, ing_id in aliases.items():
        if ing_id not in id_to_display:
            id_to_display[ing_id] = alias

    if ingredient_id in id_to_display:
        return id_to_display[ingredient_id]
    # Fallback: turn snake_case ID into a readable label
    return ingredient_id.replace("_", " ")


# ---------------------------------------------------------------------------
# B2B Tools (existing — preserved for backward compatibility)
# ---------------------------------------------------------------------------

def get_urgent_inventory(store_id: str, top_n: int = 20) -> List[dict]:
    """Fetch the most urgent (near-expiry) batches for a store, scored by real P1 priority.

    Checks p1_cache first so repeated calls within a session are free.
    On a cold cache, runs run_p1 and populates the cache.
    """
    from app.core.pipeline import p1_cache
    from app.core.pipeline.p1_priority import run_p1

    def _to_dict(item):
        """Convert P1Output to the dict format expected by the B2B agent."""
        return {
            "batch_id":        item.batch_id,
            "ingredient_id":   item.ingredient_id,
            "sku_id":          item.sku_id,
            "expiry_days":     item.expiry_days,
            "remaining_qty_g": item.remaining_qty_g,
            "priority_score":  round(item.priority_score, 4),
            "urgency_flag":    item.urgency_flag,
        }

    # Warm path: use pre-computed P1 scores from cache
    cached = p1_cache.get(store_id)
    if cached:
        top = sorted(cached, key=lambda x: x.priority_score, reverse=True)[:top_n]
        return [_to_dict(item) for item in top]

    # Cold path: run P1 and populate cache
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

    all_sku_ids = {b["sku_id"] for b in batches}
    sales_history = {sku_id: connector.get_sales_history(store_id, sku_id) for sku_id in all_sku_ids}

    p1_scores = run_p1(batches, sales_history, repo.sku_lookup(), top_n=len(batches))
    p1_cache.put(store_id, p1_scores)

    top = sorted(p1_scores, key=lambda x: x.priority_score, reverse=True)[:top_n]
    return [_to_dict(item) for item in top]


def search_recipes_from_ingredients(
    ingredient_ids: List[str],
    ingredient_urgency: Optional[dict] = None,
    top_k: int = 10,
) -> List[dict]:
    """Find recipes that best cover urgent ingredients.

    ingredient_urgency: dict mapping ingredient_id → priority_score (0.0–1.0).
    When provided, uses urgency-weighted scoring (P2 formula):
        score = max_priority + 0.3 * sum(remaining priorities)
    so recipes covering CRITICAL ingredients rank above those covering WATCH ones.
    Falls back to simple count-based scoring when ingredient_urgency is absent.
    """
    with open(FIXTURES_DIR / "mock_recipes.json", encoding="utf-8") as f:
        recipes = json.load(f)

    scored = []
    for recipe in recipes:
        recipe_ings = {ing["ingredient_id"] for ing in recipe.get("ingredients", [])}
        matched_ids = list(set(ingredient_ids) & recipe_ings)
        if not matched_ids:
            continue

        if ingredient_urgency:
            priorities = sorted(
                [ingredient_urgency.get(ing_id, 0.0) for ing_id in matched_ids],
                reverse=True,
            )
            urgency_score = round(priorities[0] + 0.3 * sum(priorities[1:]), 6)
        else:
            urgency_score = float(len(matched_ids))

        scored.append({
            "recipe_id": recipe["recipe_id"],
            "name": recipe["name"],
            "matched_count": len(matched_ids),
            "urgency_score": urgency_score,
            "matched_urgent_ingredients": [
                {
                    "ingredient_id": ing_id,
                    "priority_score": ingredient_urgency.get(ing_id, 0.0) if ingredient_urgency else 0.0,
                }
                for ing_id in sorted(matched_ids, key=lambda x: (ingredient_urgency or {}).get(x, 0.0), reverse=True)
            ],
            "ingredients": recipe["ingredients"],
        })

    scored.sort(key=lambda x: x["urgency_score"], reverse=True)
    return scored[:top_k]


def check_feasibility_and_substitute(
    recipe: dict, store_id_or_inventory = "BHX-HCM001"
) -> dict:
    """Check recipe feasibility using packet-based allocation and attempt ontology-based substitution.

    Accepts either a store_id string (fetches from connector) or an explicit inventory list (for tests).
    store_id_or_inventory: str (store ID like "BHX-HCM001") or list (explicit batches for testing).
    """
    # Accept explicit inventory list (tests) or look up via store_id
    if isinstance(store_id_or_inventory, (list, tuple)):
        full_inventory = store_id_or_inventory
    else:
        full_inventory = connector.get_batches(store_id_or_inventory)

    # Convert Pydantic models to dicts if needed
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

        # Group batches by ingredient_id
        batches = [
            b for b in inventory_dicts
            if b["ingredient_id"] == ing_id
        ]

        chosen_sub = None
        allocation = None

        if batches:
            allocation = allocate_fefo(batches, required_g=needed, strategy="best")
            if allocation.feasible:
                status = "fulfilled"
            else:
                # Primary infeasible — try ontology substitutes
                subs = query_ontology(ing_id, relation="substitute")
                status = "missing"
                for sub_id in subs.get("substitutes", []):
                    sub_batches = [b for b in inventory_dicts if b["ingredient_id"] == sub_id]
                    if not sub_batches:
                        continue
                    sub_alloc = allocate_fefo(sub_batches, required_g=needed, strategy="best")
                    if sub_alloc.feasible:
                        status = "substitute"
                        chosen_sub = sub_id
                        allocation = sub_alloc
                        break
        else:
            # No primary batches — try ontology substitutes directly
            subs = query_ontology(ing_id, relation="substitute")
            status = "missing"
            for sub_id in subs.get("substitutes", []):
                sub_batches = [b for b in inventory_dicts if b["ingredient_id"] == sub_id]
                if not sub_batches:
                    continue
                sub_alloc = allocate_fefo(sub_batches, required_g=needed, strategy="best")
                if sub_alloc.feasible:
                    status = "substitute"
                    chosen_sub = sub_id
                    allocation = sub_alloc
                    break

        if allocation is not None:
            # Always record allocation metrics, even if infeasible (for diagnostics)
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

    total = len(ingredient_status)
    fulfilled_count = sum(
        1 for s in ingredient_status if s["status"] in ("fulfilled", "substitute")
    )
    completeness = fulfilled_count / total if total > 0 else 0

    return {
        "recipe": recipe,
        "ingredient_status": ingredient_status,
        "completeness_score": round(completeness, 3),
        "feasible": completeness >= 0.7,
    }


def calculate_pricing_and_waste(bundle_data: dict) -> Optional[BundleOutput]:
    """Compute pricing and waste metrics for a bundle (placeholder for MVP)."""
    # TODO: migrate P7 pricing logic here
    return None


# ---------------------------------------------------------------------------
# Consumer Tools (new — Feature 2)
# ---------------------------------------------------------------------------

def get_user_inventory(user_id: str) -> List[dict]:
    """
    Load a consumer's home inventory from mock data.

    Returns list of UserIngredient-shaped dicts:
      {ingredient_id, quantity_g, expiry_date, expiry_days}
    """
    inventory_path = DATA_DIR / "mock_user_inventory.json"
    with open(inventory_path, encoding="utf-8") as f:
        all_users = json.load(f)

    return all_users.get(user_id, [])


def get_user_urgent_ingredients(
    user_inventory: List[dict], threshold_days: int = 3
) -> List[dict]:
    """
    Filter user inventory to items expiring within threshold_days.

    Returns items sorted by expiry_days ascending (most urgent first).
    """
    urgent = [
        item for item in user_inventory
        if item.get("expiry_days", 999) <= threshold_days
    ]
    urgent.sort(key=lambda x: x["expiry_days"])
    return urgent


def find_recipes_for_consumer(
    available_ingredients: List[dict],
    urgent_ingredients: List[dict],
    allergies: Optional[List[str]] = None,
    top_k: int = 10,
) -> List[dict]:
    """
    Score and rank recipes for a consumer, heavily prioritizing urgent ingredients.

    Scoring:
      - Each matched urgent ingredient: +3 points
      - Each matched non-urgent available ingredient: +1 point
      - Recipes containing allergens are excluded entirely.
    """
    allergies = allergies or []
    allergy_set = set(allergies)

    available_ids = {item["ingredient_id"] for item in available_ingredients}
    urgent_ids = {item["ingredient_id"] for item in urgent_ingredients}

    recipes = DataRepository.get().recipes()

    scored = []
    for recipe in recipes:
        recipe_ings = [ing["ingredient_id"] for ing in recipe.get("ingredients", [])]
        recipe_ing_set = set(recipe_ings)

        # Skip recipes containing allergens (non-optional ingredients)
        required_ings = {
            ing["ingredient_id"]
            for ing in recipe.get("ingredients", [])
            if not ing.get("is_optional", False)
        }
        if required_ings & allergy_set:
            # Check if allergen can be substituted
            can_substitute_all = True
            for allergen in required_ings & allergy_set:
                subs = query_ontology(allergen, relation="substitute")
                sub_ids = set(subs.get("substitutes", []))
                # Need at least one substitute that's available and not allergenic
                safe_subs = (sub_ids & available_ids) - allergy_set
                if not safe_subs:
                    can_substitute_all = False
                    break
            if not can_substitute_all:
                continue

        # Score: urgent matches worth 3x
        urgent_matches = recipe_ing_set & urgent_ids
        normal_matches = (recipe_ing_set & available_ids) - urgent_ids
        score = len(urgent_matches) * 3 + len(normal_matches)

        if score > 0:
            scored.append({
                "recipe_id": recipe["recipe_id"],
                "name": recipe["name"],
                "category": recipe.get("category"),
                "servings": recipe.get("servings"),
                "score": score,
                "urgent_used": list(urgent_matches),
                "available_used": list(normal_matches),
                "total_ingredients": len(recipe_ings),
                "ingredients": recipe["ingredients"],
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def adjust_recipe_for_user(
    recipe: dict,
    available_ingredients: List[dict],
    allergies: Optional[List[str]] = None,
) -> dict:
    """
    Adjust a recipe for a consumer:
      1. Replace allergens with safe substitutes from ontology.
      2. Replace unavailable required ingredients with available substitutes.
      3. Mark missing ingredients that have no substitutes.

    Returns the adjusted recipe with ingredient status annotations.
    """
    allergies = allergies or []
    allergy_set = set(allergies)
    available_map = {item["ingredient_id"]: item for item in available_ingredients}

    adjusted_ingredients = []

    for ing in recipe.get("ingredients", []):
        ing_id = ing["ingredient_id"]
        is_optional = ing.get("is_optional", False)

        # Determine if this ingredient is problematic
        is_allergen = ing_id in allergy_set
        is_available = ing_id in available_map

        if is_allergen or (not is_available and not is_optional):
            # Try to find a substitute
            subs = query_ontology(ing_id, relation="substitute")
            sub_candidates = subs.get("substitutes", [])

            # Filter: must be available AND not an allergen
            safe_available_subs = [
                s for s in sub_candidates
                if s in available_map and s not in allergy_set
            ]

            if safe_available_subs:
                chosen_sub = safe_available_subs[0]
                adjusted_ingredients.append({
                    **ing,
                    "original_ingredient_id": ing_id,
                    "ingredient_id": chosen_sub,
                    "status": "substituted",
                    "reason": "allergen" if is_allergen else "unavailable",
                })
            elif is_optional:
                adjusted_ingredients.append({
                    **ing,
                    "status": "skipped",
                    "reason": "optional_unavailable",
                })
            else:
                adjusted_ingredients.append({
                    **ing,
                    "status": "missing",
                    "reason": "allergen_no_substitute" if is_allergen else "unavailable_no_substitute",
                })
        elif is_available:
            adjusted_ingredients.append({
                **ing,
                "status": "fulfilled",
            })
        else:
            # Optional and not available
            adjusted_ingredients.append({
                **ing,
                "status": "skipped",
                "reason": "optional_unavailable",
            })

    # Only count required (non-optional) ingredients in the completeness denominator.
    # Optional ingredients that are unavailable are "skipped" and should not
    # penalize the score — they were never needed for the recipe to work.
    required_total = sum(1 for a in adjusted_ingredients if not a.get("is_optional", False))
    usable = sum(
        1 for a in adjusted_ingredients
        if a["status"] in ("fulfilled", "substituted") and not a.get("is_optional", False)
    )
    completeness = usable / required_total if required_total > 0 else 0

    return {
        "recipe_id": recipe.get("recipe_id"),
        "name": recipe.get("name"),
        "category": recipe.get("category"),
        "servings": recipe.get("servings"),
        "adjusted_ingredients": adjusted_ingredients,
        "completeness_score": round(completeness, 3),
        "feasible": completeness >= 0.7,
    }


# ---------------------------------------------------------------------------
# Shopping Mode Tools (Feature 2 Phase 2)
# ---------------------------------------------------------------------------

def get_recipe_by_name(recipe_name: str) -> Optional[dict]:
    """
    Find a recipe by its Vietnamese name.

    Performs fuzzy matching to find recipes by partial name or alias.
    Used when user knows exactly what recipe they want to cook.

    Args:
        recipe_name: Recipe name in Vietnamese (e.g., "Phở", "Thịt kho tàu")

    Returns:
        Full recipe dict with {recipe_id, name, ingredients, instructions, servings}
        or None if no recipe found.
    """
    repo = DataRepository.get()
    recipes = repo.recipes()

    # Normalize search
    search_text = recipe_name.strip().lower()

    if not search_text:
        return None

    # Exact match (case-insensitive)
    for recipe in recipes:
        if recipe["name"].lower() == search_text:
            return recipe

    # Substring match (user typed partial name or common variant)
    candidates = [
        recipe for recipe in recipes
        if search_text in recipe["name"].lower() or recipe["name"].lower() in search_text
    ]

    if len(candidates) == 1:
        return candidates[0]

    # Multiple matches — return shortest name match (most specific)
    if candidates:
        candidates.sort(key=lambda x: len(x["name"]))
        return candidates[0]

    return None


def get_remaining_ingredients(
    recipe_id: str,
    available_ingredients: List[str],
) -> Optional[dict]:
    """
    Compute what ingredients user needs to buy for a specific recipe.

    Given a recipe and list of ingredients user already has,
    returns what they need to purchase with quantities.

    Used in shopping mode when user says:
    "I want to cook [recipe]. I already have [ingredients]. What else do I need?"

    Args:
        recipe_id: Recipe ID (e.g., "R022")
        available_ingredients: List of ingredient_ids user has (e.g., ["thit_heo", "ca_chua"])

    Returns:
        Dict with:
        {
            "recipe_id": str,
            "recipe_name": str,
            "total_ingredients": int,
            "available": List[{ingredient_id, name, status}],
            "to_buy": List[{ingredient_id, name, required_qty_g, unit, is_optional}],
            "substitutable": List[{ingredient_id, name, substitutes}],
            "estimated_cost": float,
            "notes": str
        }
    """
    repo = DataRepository.get()
    recipe_lookup = repo.recipe_lookup()
    sku_lookup = repo.ingredient_sku_lookup()

    recipe = recipe_lookup.get(recipe_id)
    if not recipe:
        return None

    available_set = set(available_ingredients)
    to_buy = []
    available = []
    substitutable = []
    total_cost = 0.0

    for ing in recipe.get("ingredients", []):
        ing_id = ing["ingredient_id"]
        required_qty = ing.get("required_qty_g", 100)
        is_optional = ing.get("is_optional", False)

        if ing_id in available_set:
            available.append({
                "ingredient_id": ing_id,
                "name": get_ingredient_display_name(ing_id),
                "status": "available",
                "required_qty_g": required_qty,
            })
        else:
            # Check if substitutes exist in user's inventory
            subs = query_ontology(ing_id, relation="substitute").get("substitutes", [])
            available_subs = [s for s in subs if s in available_set]
            if available_subs:
                available.append({
                    "ingredient_id": ing_id,
                    "name": get_ingredient_display_name(ing_id),
                    "status": "substitutable",
                    "available_substitute": available_subs[0],
                    "required_qty_g": required_qty,
                })
            else:
                # Need to buy
                sku = sku_lookup.get(ing_id)
                unit_price = sku.get("retail_price", 0) if sku else 0

                to_buy.append({
                    "ingredient_id": ing_id,
                    "name": get_ingredient_display_name(ing_id),
                    "required_qty_g": required_qty,
                    "unit": "g",
                    "is_optional": is_optional,
                    "estimated_unit_price": unit_price,
                    "sku_id": sku.get("sku_id") if sku else None,
                })
                total_cost += unit_price

                if subs:
                    substitutable.append({
                        "ingredient_id": ing_id,
                        "name": get_ingredient_display_name(ing_id),
                        "substitutes": [
                            {"id": s, "name": get_ingredient_display_name(s)}
                            for s in subs
                        ],
                    })

    return {
        "recipe_id": recipe_id,
        "recipe_name": recipe.get("name", "Unknown"),
        "servings": recipe.get("servings", 4),
        "total_ingredients": len(recipe.get("ingredients", [])),
        "available_count": len(available),
        "to_buy": to_buy,
        "available": available,
        "substitutable": substitutable,
        "estimated_cost": round(total_cost, 2),
        "notes": f"Nấu {recipe.get('name')} cho {recipe.get('servings', 4)} người",
    }


def get_ingredient_suggestions(
    recipe_id: str,
    available_ingredients: List[str],
) -> Optional[dict]:
    """
    Get smart ingredient suggestions for a recipe user wants to cook.

    Analyzes what user has vs. what recipe needs, and suggests:
    - Substitutes for missing ingredients (using ontology)
    - Alternatives that are cheaper or more available
    - Quantity adjustments based on servings

    Args:
        recipe_id: Recipe ID
        available_ingredients: Ingredients user has

    Returns:
        Dict with suggestions including substitutes, alternatives, and notes
    """
    repo = DataRepository.get()
    recipe_lookup = repo.recipe_lookup()

    recipe = recipe_lookup.get(recipe_id)
    if not recipe:
        return None

    available_set = set(available_ingredients)
    suggestions = {
        "recipe_id": recipe_id,
        "recipe_name": recipe.get("name"),
        "substitutes": [],
        "alternatives": [],
        "notes": [],
    }

    for ing in recipe.get("ingredients", []):
        ing_id = ing["ingredient_id"]

        if ing_id not in available_set:
            # Find substitutes using ontology
            subs = query_ontology(ing_id, relation="substitute").get("substitutes", [])

            if subs:
                suggestions["substitutes"].append({
                    "missing_ingredient_id": ing_id,
                    "missing_ingredient_name": get_ingredient_display_name(ing_id),
                    "suggested_substitutes": [
                        {
                            "ingredient_id": sub_id,
                            "name": get_ingredient_display_name(sub_id),
                            "reason": "Thay thế tương đương",
                            "availability": "available" if sub_id in available_set else "need_to_buy",
                        }
                        for sub_id in subs
                    ],
                })
            else:
                suggestions["notes"].append(
                    f"Không có thay thế cho {get_ingredient_display_name(ing_id)}"
                )

    # Add general notes
    total_missing = len([
        ing for ing in recipe.get("ingredients", [])
        if ing["ingredient_id"] not in available_set
    ])

    if total_missing == 0:
        suggestions["notes"].append("✓ Bạn đã có đủ nguyên liệu nấu món này!")
    elif total_missing <= 2:
        suggestions["notes"].append(f"Chỉ cần mua thêm {total_missing} nguyên liệu")
    else:
        suggestions["notes"].append(f"Cần mua thêm {total_missing} nguyên liệu")

    return suggestions


# ---------------------------------------------------------------------------
# Tool registries
# ---------------------------------------------------------------------------

# B2B tools (used by B2B agent graph)
b2b_tools = [
    get_urgent_inventory,
    search_recipes_from_ingredients,
    check_feasibility_and_substitute,
    calculate_pricing_and_waste,
    query_ontology,
]

# Consumer tools (used by Consumer agent graph)
# Includes discovery mode (find what to cook) and shopping mode (find what to buy)
consumer_tools = [
    # Discovery mode: "I don't know what to cook"
    resolve_ingredient_names,
    get_user_inventory,
    get_user_urgent_ingredients,
    find_recipes_for_consumer,
    adjust_recipe_for_user,
    # Shopping mode: "I want to cook this recipe"
    get_recipe_by_name,
    get_remaining_ingredients,
    get_ingredient_suggestions,
    # Shared
    query_ontology,
]

# Combined for backward compatibility
tools = b2b_tools
