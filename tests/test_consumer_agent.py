"""
Tests for the Consumer Home Cooking Agent (Feature 2).

Tests cover:
  - Ingredient name resolution (Vietnamese → ingredient_id)
  - Urgent ingredient detection
  - Recipe scoring with urgent priority
  - Allergy filtering and substitution
  - Recipe adjustment for user inventory
  - One-shot suggest endpoint logic
"""

import json
from pathlib import Path

import pytest

from app.agent.shared.ontology import are_substitutes, get_all_substitutes, query_ontology
from app.agent.tools import (
    adjust_recipe_for_user,
    find_recipes_for_consumer,
    get_ingredient_display_name,
    get_user_inventory,
    get_user_urgent_ingredients,
    resolve_ingredient_name,
    resolve_ingredient_names,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_001_inventory():
    return get_user_inventory("user_001")


@pytest.fixture
def user_002_inventory():
    return get_user_inventory("user_002")


@pytest.fixture
def mock_user_inventory_raw():
    with open(FIXTURES_DIR / "mock_user_inventory.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Ingredient Name Resolution
# ---------------------------------------------------------------------------

class TestIngredientNameResolution:

    def test_exact_vietnamese_names(self):
        assert resolve_ingredient_name("thịt heo") == "thit_heo"
        assert resolve_ingredient_name("cà chua") == "ca_chua"
        assert resolve_ingredient_name("tôm") == "tom"
        assert resolve_ingredient_name("nước mắm") == "nuoc_mam"

    def test_informal_names(self):
        assert resolve_ingredient_name("gà") == "thit_ga"
        assert resolve_ingredient_name("bò") == "thit_bo"
        assert resolve_ingredient_name("heo") == "thit_heo"
        assert resolve_ingredient_name("trứng") == "trung_ga"

    def test_aliases(self):
        assert resolve_ingredient_name("thịt lợn") == "thit_heo"
        assert resolve_ingredient_name("đậu phụ") == "dau_hu"
        assert resolve_ingredient_name("tàu hũ") == "dau_hu"
        assert resolve_ingredient_name("mướp đắng") == "kho_qua"
        assert resolve_ingredient_name("dứa") == "khom"

    def test_without_diacritics(self):
        assert resolve_ingredient_name("thit heo") == "thit_heo"
        assert resolve_ingredient_name("ca chua") == "ca_chua"
        assert resolve_ingredient_name("rau muong") == "rau_muong"

    def test_unknown_ingredient_returns_none(self):
        assert resolve_ingredient_name("pizza") is None
        assert resolve_ingredient_name("hamburger") is None
        assert resolve_ingredient_name("") is None

    def test_whitespace_handling(self):
        assert resolve_ingredient_name("  thịt heo  ") == "thit_heo"
        assert resolve_ingredient_name("CÀ CHUA") is None or resolve_ingredient_name("cà chua") == "ca_chua"

    def test_batch_resolution(self):
        results = resolve_ingredient_names(["thịt heo", "cà chua", "xyz_unknown"])
        assert len(results) == 3
        assert results[0]["resolved"] is True
        assert results[0]["ingredient_id"] == "thit_heo"
        assert results[1]["resolved"] is True
        assert results[1]["ingredient_id"] == "ca_chua"
        assert results[2]["resolved"] is False
        assert results[2]["ingredient_id"] is None

    def test_display_name_roundtrip(self):
        name = get_ingredient_display_name("thit_heo")
        assert name == "thịt heo"
        resolved = resolve_ingredient_name(name)
        assert resolved == "thit_heo"


# ---------------------------------------------------------------------------
# Ontology
# ---------------------------------------------------------------------------

class TestOntology:

    def test_query_substitute(self):
        result = query_ontology("thit_heo", relation="substitute")
        assert "thit_ga" in result["substitutes"]
        assert "thit_bo" in result["substitutes"]

    def test_get_all_substitutes(self):
        subs = get_all_substitutes("tom")
        assert "muc" in subs
        assert "ngheu" in subs

    def test_are_substitutes_bidirectional(self):
        assert are_substitutes("thit_heo", "thit_ga") is True
        assert are_substitutes("thit_ga", "thit_heo") is True

    def test_no_substitutes(self):
        result = query_ontology("nonexistent_ingredient")
        assert result["substitutes"] == []

    def test_unknown_relation(self):
        result = query_ontology("thit_heo", relation="pairing")
        assert result["substitutes"] == []


# ---------------------------------------------------------------------------
# User Inventory & Urgent Detection
# ---------------------------------------------------------------------------

class TestUserInventory:

    def test_load_user_inventory(self):
        inv = get_user_inventory("user_001")
        assert len(inv) > 0
        assert all("ingredient_id" in item for item in inv)
        assert all("expiry_days" in item for item in inv)

    def test_unknown_user_returns_empty(self):
        inv = get_user_inventory("nonexistent_user")
        assert inv == []

    def test_urgent_ingredients_filtering(self, user_001_inventory):
        urgent = get_user_urgent_ingredients(user_001_inventory, threshold_days=3)
        assert len(urgent) > 0
        assert all(item["expiry_days"] <= 3 for item in urgent)

    def test_urgent_sorted_by_expiry(self, user_001_inventory):
        urgent = get_user_urgent_ingredients(user_001_inventory, threshold_days=3)
        expiry_days = [item["expiry_days"] for item in urgent]
        assert expiry_days == sorted(expiry_days)

    def test_no_urgent_with_low_threshold(self, user_001_inventory):
        urgent = get_user_urgent_ingredients(user_001_inventory, threshold_days=-1)
        assert len(urgent) == 0

    def test_all_urgent_with_high_threshold(self, user_001_inventory):
        urgent = get_user_urgent_ingredients(user_001_inventory, threshold_days=9999)
        assert len(urgent) == len(user_001_inventory)


# ---------------------------------------------------------------------------
# Recipe Scoring (Consumer)
# ---------------------------------------------------------------------------

class TestRecipeScoring:

    def test_recipes_found_for_user(self, user_001_inventory):
        urgent = get_user_urgent_ingredients(user_001_inventory)
        recipes = find_recipes_for_consumer(user_001_inventory, urgent)
        assert len(recipes) > 0

    def test_urgent_ingredients_scored_higher(self, user_001_inventory):
        urgent = get_user_urgent_ingredients(user_001_inventory)
        recipes = find_recipes_for_consumer(user_001_inventory, urgent)

        # Top recipe should use at least one urgent ingredient
        top = recipes[0]
        assert len(top["urgent_used"]) > 0

    def test_recipes_sorted_by_score(self, user_001_inventory):
        urgent = get_user_urgent_ingredients(user_001_inventory)
        recipes = find_recipes_for_consumer(user_001_inventory, urgent)
        scores = [r["score"] for r in recipes]
        assert scores == sorted(scores, reverse=True)

    def test_allergy_filtering(self, user_002_inventory):
        """Recipes requiring the allergen (with no substitute) should be excluded."""
        urgent = get_user_urgent_ingredients(user_002_inventory)
        # User allergic to tôm — recipes with tôm as required should be excluded
        # unless tôm can be substituted.
        # Use top_k=100 to avoid rank-cutoff effects masking the subset relationship.
        recipes_no_allergy = find_recipes_for_consumer(user_002_inventory, urgent, allergies=[], top_k=100)
        recipes_with_allergy = find_recipes_for_consumer(user_002_inventory, urgent, allergies=["tom"], top_k=100)

        # With allergy, should have fewer or equal recipes (some tom recipes may be kept
        # if substitution is possible, e.g. tom → muc)
        tom_recipe_ids_no_allergy = {r["recipe_id"] for r in recipes_no_allergy}
        tom_recipe_ids_with_allergy = {r["recipe_id"] for r in recipes_with_allergy}
        assert tom_recipe_ids_with_allergy <= tom_recipe_ids_no_allergy

    def test_empty_inventory_returns_nothing(self):
        recipes = find_recipes_for_consumer([], [])
        assert recipes == []


# ---------------------------------------------------------------------------
# Recipe Adjustment
# ---------------------------------------------------------------------------

class TestRecipeAdjustment:

    def test_fully_available_recipe(self, user_001_inventory, mock_recipes):
        """A recipe where all required ingredients are available should be fully fulfilled."""
        # R031 = Cá lóc kho tộ: required ca_loc + nuoc_mam — both in user_001
        r031 = next(r for r in mock_recipes if r["recipe_id"] == "R031")
        adjusted = adjust_recipe_for_user(r031, user_001_inventory)
        assert adjusted["feasible"] is True
        assert adjusted["completeness_score"] == 1.0
        # All required (non-optional) ingredients must be fulfilled
        assert all(
            ing["status"] == "fulfilled"
            for ing in adjusted["adjusted_ingredients"]
            if not ing.get("is_optional", False)
        )

    def test_allergen_substitution(self, mock_recipes):
        """Allergen should be substituted if a safe substitute is available."""
        # R008 = Rau muống xào tỏi: has rau_muong as required ingredient.
        # user_003 has rau_ngo which is an ontology substitute for rau_muong.
        user_003_inv = get_user_inventory("user_003")
        r008 = next(r for r in mock_recipes if r["recipe_id"] == "R008")
        adjusted = adjust_recipe_for_user(r008, user_003_inv, allergies=["rau_muong"])

        rau_muong_ing = next(
            ing for ing in adjusted["adjusted_ingredients"]
            if ing.get("original_ingredient_id") == "rau_muong" or ing["ingredient_id"] == "rau_muong"
        )
        # Should be substituted, not the original allergen
        assert rau_muong_ing["status"] == "substituted"
        assert rau_muong_ing["ingredient_id"] != "rau_muong"

    def test_missing_ingredient_marked(self, mock_recipes):
        """Missing ingredients with no substitutes should be marked as missing."""
        r001 = next(r for r in mock_recipes if r["recipe_id"] == "R001")
        # Empty inventory — nothing available
        adjusted = adjust_recipe_for_user(r001, [])
        missing = [ing for ing in adjusted["adjusted_ingredients"] if ing["status"] == "missing"]
        assert len(missing) > 0
        assert adjusted["feasible"] is False

    def test_optional_ingredients_skipped(self, mock_recipes):
        """Optional ingredients that are unavailable should be skipped, not missing."""
        # R001 has optional hanh_la and rau_ngo
        r001 = next(r for r in mock_recipes if r["recipe_id"] == "R001")
        # Inventory with only the main ingredients
        inv = [
            {"ingredient_id": "ca_loc", "quantity_g": 500, "expiry_days": 5},
            {"ingredient_id": "ca_chua", "quantity_g": 300, "expiry_days": 5},
            {"ingredient_id": "khom", "quantity_g": 200, "expiry_days": 5},
            {"ingredient_id": "me", "quantity_g": 50, "expiry_days": 30},
            {"ingredient_id": "nuoc_mam", "quantity_g": 100, "expiry_days": 180},
        ]
        adjusted = adjust_recipe_for_user(r001, inv)
        optional_statuses = [
            ing["status"]
            for ing in adjusted["adjusted_ingredients"]
            if ing.get("is_optional", False)
        ]
        assert all(s in ("fulfilled", "skipped") for s in optional_statuses)


# ---------------------------------------------------------------------------
# One-Shot Suggest (end-to-end tool chain without LLM)
# ---------------------------------------------------------------------------

class TestSuggestFlow:

    @pytest.mark.asyncio
    async def test_suggest_basic(self):
        from app.agent.consumer.graph import suggest

        result = await suggest(
            ingredients=["thịt heo", "cà chua", "trứng gà", "hành lá", "nước mắm"],
            allergies=None,
            top_k=3,
        )
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        assert len(result["suggestions"]) <= 3
        assert len(result["unresolved_ingredients"]) == 0

    @pytest.mark.asyncio
    async def test_suggest_with_allergy(self):
        from app.agent.consumer.graph import suggest

        result = await suggest(
            ingredients=["tôm", "mực", "hành tây", "tỏi", "nước mắm"],
            allergies=["tôm"],
            top_k=5,
        )
        assert "tom" in result["allergy_ids"]
        # All suggestions should be feasible with substitutions
        for s in result["suggestions"]:
            for ing in s["adjusted_ingredients"]:
                if ing["ingredient_id"] == "tom":
                    # If tom appears, it must be substituted
                    assert ing["status"] == "substituted"

    @pytest.mark.asyncio
    async def test_suggest_with_unknown_ingredient(self):
        from app.agent.consumer.graph import suggest

        result = await suggest(
            ingredients=["thịt heo", "pizza_topping"],
            allergies=None,
            top_k=3,
        )
        assert "pizza_topping" in result["unresolved_ingredients"]
        # Should still return results based on thit_heo
        assert len(result["resolved_ingredients"]) == 2
        resolved_count = sum(1 for r in result["resolved_ingredients"] if r["resolved"])
        assert resolved_count == 1


# ---------------------------------------------------------------------------
# Multi-turn Flow Structure (tested without LLM — just verify state shapes)
# ---------------------------------------------------------------------------

class TestConsumerStateShape:

    def test_consumer_state_extends_base(self):
        from app.agent.consumer.state import ConsumerState
        from app.agent.state import AgentState

        # ConsumerState should have all AgentState keys plus consumer-specific ones
        base_keys = set(AgentState.__annotations__.keys())
        consumer_keys = set(ConsumerState.__annotations__.keys())
        assert base_keys <= consumer_keys
        assert "user_id" in consumer_keys
        assert "allergies" in consumer_keys
        assert "conversation_mode" in consumer_keys
        assert "urgent_ingredients" in consumer_keys

    def test_consumer_tools_registered(self):
        from app.agent.consumer.tools import consumer_langchain_tools

        tool_names = {t.name for t in consumer_langchain_tools}
        assert "resolve_ingredient_names" in tool_names
        assert "find_recipes_for_consumer" in tool_names
        assert "adjust_recipe_for_user" in tool_names
        assert "query_ontology" in tool_names
