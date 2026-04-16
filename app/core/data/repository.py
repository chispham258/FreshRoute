"""
DataRepository — Single source of truth for all static reference data.

Implements Singleton pattern with lazy loading + caching for:
- SKUs (from app/data/skus.py)
- Recipes (from app/data/recipes.py)
- Substitute groups (JSON)
- Ingredient aliases (JSON)
- Default weights (JSON)
- Category margins (JSON)
- Derived: inverted index, SKU lookups, recipe requirements, recipe names
"""

import json
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Optional

from app.core.data.skus import SKUS
from app.core.data.recipes import RECIPES
from app.core.models.inventory import ProductSKU
from app.core.pipeline.p2_retrieval import load_inverted_index_from_recipes


DATA_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures"


class DataRepository:
    """
    Singleton repository for all static data.

    Lazy-loads and caches all reference data on first access.
    """

    _instance: Optional["DataRepository"] = None
    _skus: Optional[List[dict]] = None
    _recipes: Optional[List[dict]] = None
    _substitute_groups: Optional[Dict] = None
    _ingredient_aliases: Optional[Dict] = None
    _default_weights: Optional[Dict] = None
    _category_margins: Optional[Dict] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get(cls) -> "DataRepository":
        """Get singleton instance."""
        return cls()

    def skus(self) -> List[dict]:
        """Get all SKUs (from app/data/skus.py)."""
        if self._skus is None:
            self._skus = SKUS
        return self._skus

    def recipes(self) -> List[dict]:
        """Get all recipes (from app/data/recipes.py)."""
        if self._recipes is None:
            self._recipes = RECIPES
        return self._recipes

    def substitute_groups(self) -> Dict:
        """Get ingredient substitute groups (from JSON)."""
        if self._substitute_groups is None:
            path = DATA_DIR / "substitute_groups.json"
            with open(path, encoding="utf-8") as f:
                self._substitute_groups = json.load(f)
        return self._substitute_groups

    def ingredient_aliases(self) -> Dict:
        """Get Vietnamese ingredient name aliases (from JSON)."""
        if self._ingredient_aliases is None:
            path = DATA_DIR / "ingredient_aliases.json"
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                # Flatten nested structure into single flat dict
                self._ingredient_aliases = {}
                for category, aliases in data.items():
                    if category != "_comment":
                        self._ingredient_aliases.update(aliases)
        return self._ingredient_aliases

    def default_weights(self) -> Dict:
        """Get default ranking weights (from JSON)."""
        if self._default_weights is None:
            path = DATA_DIR / "default_weights.json"
            with open(path, encoding="utf-8") as f:
                self._default_weights = json.load(f)
        return self._default_weights

    def category_margins(self) -> Dict:
        """Get category profit margins (from JSON)."""
        if self._category_margins is None:
            path = DATA_DIR / "category_margins.json"
            with open(path, encoding="utf-8") as f:
                self._category_margins = json.load(f)
        return self._category_margins

    # ===== Derived Lookups (cached computations) =====

    @lru_cache(maxsize=1)
    def inverted_index(self) -> Dict[str, List[str]]:
        """Build inverted index: ingredient_id → recipe_ids."""
        recipes = self.recipes()
        return load_inverted_index_from_recipes(recipes)

    @lru_cache(maxsize=1)
    def sku_lookup(self) -> Dict[str, ProductSKU]:
        """Build SKU lookup: {sku_id: ProductSKU}."""
        skus = self.skus()
        lookup = {}
        for s in skus:
            lookup[s["sku_id"]] = ProductSKU(**s)
        return lookup

    @lru_cache(maxsize=1)
    def sku_dict_lookup(self) -> Dict[str, dict]:
        """Build SKU dict lookup: {sku_id: dict}."""
        skus = self.skus()
        return {s["sku_id"]: s for s in skus}

    @lru_cache(maxsize=1)
    def recipe_requirements(self) -> Dict[str, List[dict]]:
        """Extract recipe requirements: {recipe_id: [ingredients]}."""
        recipes = self.recipes()
        return {r["recipe_id"]: r["ingredients"] for r in recipes}

    @lru_cache(maxsize=1)
    def recipe_names(self) -> Dict[str, str]:
        """Extract recipe names: {recipe_id: name}."""
        recipes = self.recipes()
        return {r["recipe_id"]: r["name"] for r in recipes}

    @lru_cache(maxsize=1)
    def recipe_lookup(self) -> Dict[str, dict]:
        """Build full recipe lookup: {recipe_id: full_recipe}."""
        recipes = self.recipes()
        return {r["recipe_id"]: r for r in recipes}
