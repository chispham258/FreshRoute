"""
Ingredient ontology utilities.

Wraps app/data/substitute_groups.json to provide a query interface
for ingredient substitution and relationship lookups.
"""

import json
from pathlib import Path
from typing import Optional

# Find project root (where app/ is located)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "app" / "core" / "data"

_substitute_cache: Optional[dict] = None


def _load_substitutes() -> dict:
    global _substitute_cache
    if _substitute_cache is None:
        with open(_DATA_DIR / "substitute_groups.json", encoding="utf-8") as f:
            _substitute_cache = json.load(f)
    return _substitute_cache


def query_ontology(ingredient_id: str, relation: str = "substitute") -> dict:
    """
    Query the ingredient ontology for relationships.

    Args:
        ingredient_id: The ingredient to look up.
        relation: Type of relation — currently supports "substitute".

    Returns:
        dict with ingredient_id and matching relations list.
    """
    subs_map = _load_substitutes()

    if relation == "substitute":
        substitutes = subs_map.get(ingredient_id, [])
        return {
            "ingredient_id": ingredient_id,
            "relation": "substitute",
            "substitutes": substitutes,
        }

    return {
        "ingredient_id": ingredient_id,
        "relation": relation,
        "substitutes": [],
    }


def get_all_substitutes(ingredient_id: str) -> list[str]:
    """Return flat list of substitute ingredient IDs."""
    result = query_ontology(ingredient_id, relation="substitute")
    return result["substitutes"]


def are_substitutes(ing_a: str, ing_b: str) -> bool:
    """Check if two ingredients are substitutes for each other."""
    subs_map = _load_substitutes()
    return ing_b in subs_map.get(ing_a, []) or ing_a in subs_map.get(ing_b, [])
