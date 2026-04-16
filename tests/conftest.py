import json
from pathlib import Path

import pytest

from app.core.models.inventory import ProductSKU

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def mock_skus():
    with open(FIXTURES_DIR / "mock_skus.json") as f:
        return json.load(f)


@pytest.fixture
def mock_inventory():
    with open(FIXTURES_DIR / "mock_inventory.json") as f:
        data = json.load(f)
    # For backward compatibility: add remaining_qty_g if not present
    for item in data:
        if "remaining_qty_g" not in item and "unit_count" in item and "pack_size_g" in item:
            item["remaining_qty_g"] = item["unit_count"] * item["pack_size_g"]
    return data


@pytest.fixture
def mock_recipes():
    with open(FIXTURES_DIR / "mock_recipes.json") as f:
        return json.load(f)


@pytest.fixture
def sku_lookup(mock_skus):
    return {s["sku_id"]: ProductSKU(**s) for s in mock_skus}


@pytest.fixture
def sku_dict_lookup(mock_skus):
    return {s["sku_id"]: s for s in mock_skus}


@pytest.fixture
def substitute_groups():
    with open(Path(__file__).resolve().parent.parent / "app" / "core" / "data" / "substitute_groups.json") as f:
        return json.load(f)


@pytest.fixture
def recipe_requirements(mock_recipes):
    return {r["recipe_id"]: r["ingredients"] for r in mock_recipes}


@pytest.fixture
def inverted_index(mock_recipes):
    from app.core.pipeline.p2_retrieval import load_inverted_index_from_recipes
    return load_inverted_index_from_recipes(mock_recipes)
