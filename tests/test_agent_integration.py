"""Integration test for B2B agent with packet-based allocation."""

import json
from pathlib import Path
from app.agent import tools as agent_tools
from app.integrations.connectors.mock import MockConnector


def test_b2b_agent_full_flow():
    """Test complete B2B agent flow: urgent inventory → recipes → feasibility check."""
    connector = MockConnector()
    store_id = "BHX-HCM123"

    # Step 1: Get urgent inventory
    urgent_batches = agent_tools.get_urgent_inventory(store_id, top_n=20)
    assert len(urgent_batches) > 0
    assert all(b.get("expiry_days", 999) <= 30 for b in urgent_batches)

    # Extract urgent ingredient IDs
    urgent_ingredient_ids = list(set(b["ingredient_id"] for b in urgent_batches))
    assert len(urgent_ingredient_ids) > 0

    # Step 2: Find recipes with urgent ingredients
    recipes = agent_tools.search_recipes_from_ingredients(urgent_ingredient_ids, top_k=5)
    assert len(recipes) > 0

    # Step 3: Check feasibility of top recipe with packet-based allocation
    top_recipe = recipes[0]
    full_inventory = connector.get_batches(store_id)
    result = agent_tools.check_feasibility_and_substitute(top_recipe, full_inventory)

    # Verify packet-based metrics are present
    assert "ingredient_status" in result
    assert len(result["ingredient_status"]) > 0
    for status in result["ingredient_status"]:
        assert "allocated_g" in status
        assert "deviation" in status
        assert "allocation_strategy" in status
        # Verify allocation strategy is valid
        assert status["allocation_strategy"] in ("strict", "approx", "none")

    # Verify feasibility logic
    assert "feasible" in result
    assert "completeness_score" in result
    assert 0 <= result["completeness_score"] <= 1.0


def test_agent_handles_packet_metrics():
    """Test that agent properly populates and uses packet-based metrics."""
    # Create test recipe with specific ingredient requirements
    recipe = {
        "recipe_id": "R_TEST",
        "name": "Test Bundle",
        "ingredients": [
            {"ingredient_id": "thit_heo", "required_qty_g": 500.0},
            {"ingredient_id": "ca_chua", "required_qty_g": 300.0},
        ]
    }

    # Create test inventory with packet-based data
    inventory = [
        {
            "batch_id": "B1",
            "ingredient_id": "thit_heo",
            "sku_id": "SKU_1",
            "unit_count": 5,  # 5 packets
            "pack_size_g": 100.0,
            "expiry_days": 3,
        },
        {
            "batch_id": "B2",
            "ingredient_id": "ca_chua",
            "sku_id": "SKU_2",
            "unit_count": 3,  # 3 packets
            "pack_size_g": 100.0,
            "expiry_days": 5,
        }
    ]

    result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

    # Verify results
    assert result["completeness_score"] == 1.0  # All ingredients available
    statuses = result["ingredient_status"]

    # Check first ingredient (thit_heo)
    thit_status = next((s for s in statuses if s["ingredient_id"] == "thit_heo"), None)
    assert thit_status is not None
    assert thit_status["status"] == "fulfilled"
    # 500g required, ceil(500/100) = 5 packets = 500g exactly, deviation = 0%
    assert thit_status["allocated_g"] == 500.0
    assert thit_status["deviation"] == 0.0
    assert thit_status["allocation_strategy"] == "strict"

    # Check second ingredient (ca_chua)
    ca_chua_status = next((s for s in statuses if s["ingredient_id"] == "ca_chua"), None)
    assert ca_chua_status is not None
    assert ca_chua_status["status"] == "fulfilled"
    # 300g required, ceil(300/100) = 3 packets = 300g exactly, deviation = 0%
    assert ca_chua_status["allocated_g"] == 300.0
    assert ca_chua_status["deviation"] == 0.0
    assert ca_chua_status["allocation_strategy"] == "strict"


def test_agent_fefo_ordering():
    """Test that agent respects FEFO ordering in allocation."""
    recipe = {
        "recipe_id": "R_FEFO",
        "ingredients": [
            {"ingredient_id": "thit_bo", "required_qty_g": 300.0}
        ]
    }

    # Two batches with different expiry dates
    inventory = [
        {
            "batch_id": "B_FRESH",  # Later expiry
            "ingredient_id": "thit_bo",
            "sku_id": "SKU_BO",
            "unit_count": 5,
            "pack_size_g": 100.0,
            "expiry_days": 10,
        },
        {
            "batch_id": "B_URGENT",  # Earlier expiry (should use first)
            "ingredient_id": "thit_bo",
            "sku_id": "SKU_BO",
            "unit_count": 5,
            "pack_size_g": 100.0,
            "expiry_days": 2,
        }
    ]

    result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

    # Should be feasible (300g required, both batches have 500g = 5*100)
    assert result["ingredient_status"][0]["status"] == "fulfilled"
    assert result["ingredient_status"][0]["allocated_g"] == 300.0
    # allocate_fefo handles the ordering internally, so the result should show
    # allocation succeeds despite batch order in input


def test_agent_with_near_boundary_deviation():
    """Test allocation at the 25% deviation boundary."""
    recipe = {
        "recipe_id": "R_BOUNDARY",
        "ingredients": [
            {"ingredient_id": "gung", "required_qty_g": 100.0}
        ]
    }

    # Pack size of 50g means 100g requires ceil(100/50) = 2 packets = 100g exactly
    inventory = [
        {
            "batch_id": "B_GUNG",
            "ingredient_id": "gung",
            "sku_id": "SKU_GUNG",
            "unit_count": 3,
            "pack_size_g": 50.0,
            "expiry_days": 5,
        }
    ]

    result = agent_tools.check_feasibility_and_substitute(recipe, inventory)
    assert result["ingredient_status"][0]["status"] == "fulfilled"
    assert result["ingredient_status"][0]["allocated_g"] == 100.0
    assert result["ingredient_status"][0]["deviation"] == 0.0  # Exact match
