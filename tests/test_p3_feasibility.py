from app.core.pipeline.p3_feasibility import (
    build_ingredient_batches,
    check_ingredient,
    run_p3,
)


def test_build_ingredient_batches_sorted_fefo():
    inventory = [
        {"batch_id": "B1", "sku_id": "S1", "ingredient_id": "thit_heo", "remaining_qty_g": 300, "expiry_days": 5},
        {"batch_id": "B2", "sku_id": "S1", "ingredient_id": "thit_heo", "remaining_qty_g": 200, "expiry_days": 1},
    ]
    grouped = build_ingredient_batches(inventory)
    assert grouped["thit_heo"][0]["batch_id"] == "B2"  # nearer expiry first


def test_get_available_qty_fefo():
    """Test packet-based FEFO allocation via check_ingredient."""
    batches = {
        "thit_heo": [
            {"batch_id": "B1", "sku_id": "S1", "ingredient_id": "thit_heo", "remaining_qty_g": 100, "expiry_days": 1, "unit_count": 1, "pack_size_g": 100},
            {"batch_id": "B2", "sku_id": "S1", "ingredient_id": "thit_heo", "remaining_qty_g": 400, "expiry_days": 5, "unit_count": 4, "pack_size_g": 100},
        ]
    }
    result = check_ingredient("thit_heo", 300, False, batches, {})
    # With packet-based allocation, 300g needs ceil(300/100) = 3 packets = 300g (exact match)
    assert result["status"] == "fulfilled"
    assert result["allocated_g"] >= 300  # Should allocate at least 300g
    assert result["deviation"] <= 0.25  # Within tolerance
    assert len(result["batches_used"]) >= 1  # At least 1 batch used


def test_check_ingredient_fulfilled():
    batches = {"thit_heo": [{"batch_id": "B1", "sku_id": "S1", "ingredient_id": "thit_heo", "remaining_qty_g": 500, "expiry_days": 2, "unit_count": 5, "pack_size_g": 100}]}
    result = check_ingredient("thit_heo", 300, False, batches, {})
    assert result["status"] == "fulfilled"
    assert result["allocated_g"] >= 300


def test_check_ingredient_substitute():
    batches = {"thit_ga": [{"batch_id": "B1", "sku_id": "S2", "ingredient_id": "thit_ga", "remaining_qty_g": 500, "expiry_days": 3, "unit_count": 5, "pack_size_g": 100}]}
    subs = {"thit_heo": ["thit_ga"]}
    result = check_ingredient("thit_heo", 300, False, batches, subs)
    assert result["status"] == "substitute"
    assert result["substitute_id"] == "thit_ga"
    assert result["allocated_g"] >= 300


def test_check_ingredient_skip_optional():
    result = check_ingredient("hanh_la", 20, True, {}, {})
    assert result["status"] == "skip"


def test_check_ingredient_missing_required():
    result = check_ingredient("thit_heo", 300, False, {}, {})
    assert result["status"] == "missing"


def test_run_p3_filters_infeasible(
    mock_inventory, sku_lookup, inverted_index, mock_recipes,
    recipe_requirements, substitute_groups,
):
    from app.core.pipeline.p1_priority import run_p1
    from app.core.pipeline.p2_retrieval import run_p2

    p1_output = run_p1(mock_inventory, {}, sku_lookup, top_n=20)
    recipe_lookup = {r["recipe_id"]: r for r in mock_recipes}
    p2_output = run_p2(p1_output, inverted_index, recipe_lookup, top_k=20)

    result = run_p3(p2_output, recipe_requirements, mock_inventory, substitute_groups)

    # Should have fewer or equal candidates than P2
    assert len(result) <= len(p2_output)
    # All should have completeness_score
    assert all("completeness_score" in r for r in result)
    # No missing ingredients
    for r in result:
        for s in r["ingredient_status"]:
            assert s["status"] != "missing"
