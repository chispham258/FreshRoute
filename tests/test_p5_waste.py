from app.core.pipeline.p5_waste import compute_waste_score, run_p5


def test_compute_waste_score_fulfilled_only():
    matched = [
        {"ingredient_id": "thit_heo", "priority_score": 0.9},
        {"ingredient_id": "ca_chua", "priority_score": 0.6},
    ]
    ingredient_status = [
        {"ingredient_id": "thit_heo", "status": "fulfilled", "batches_used": [
            {"batch_id": "B1", "sku_id": "SKU-M001", "qty_taken_g": 400}
        ]},
        {"ingredient_id": "ca_chua", "status": "substitute", "batches_used": [
            {"batch_id": "B2", "sku_id": "SKU-V003", "qty_taken_g": 200}
        ]},
    ]
    sku_lookup = {
        "SKU-M001": {"cost_price": 68000, "pack_size_g": 500},
        "SKU-V003": {"cost_price": 12000, "pack_size_g": 500},
    }

    score = compute_waste_score(matched, ingredient_status, sku_lookup)
    # Only thit_heo counted (fulfilled), not ca_chua (substitute)
    expected = 0.9 * (68000 / 500) * 400  # 0.9 * 136 * 400 = 48960
    assert abs(score - expected) < 1


def test_run_p5_normalizes():
    p3_output = [
        {
            "recipe_id": "R1", "matched_ingredients": [{"ingredient_id": "x", "priority_score": 0.9}],
            "ingredient_status": [{"ingredient_id": "x", "status": "fulfilled",
                                   "batches_used": [{"batch_id": "B1", "sku_id": "S1", "qty_taken_g": 100}]}],
        },
        {
            "recipe_id": "R2", "matched_ingredients": [{"ingredient_id": "x", "priority_score": 0.5}],
            "ingredient_status": [{"ingredient_id": "x", "status": "fulfilled",
                                   "batches_used": [{"batch_id": "B2", "sku_id": "S1", "qty_taken_g": 100}]}],
        },
    ]
    sku_lookup = {"S1": {"cost_price": 10000, "pack_size_g": 100}}
    result = run_p5(p3_output, sku_lookup)

    # Higher waste_score should normalize to 1.0
    assert result[0]["waste_score_normalized"] == 1.0
    assert 0 < result[1]["waste_score_normalized"] < 1.0
