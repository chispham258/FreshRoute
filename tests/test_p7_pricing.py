from app.core.pipeline.p7_pricing import apply_discount, compute_bundle_prices, compute_weighted_min_margin


def test_compute_bundle_prices():
    ingredient_status = [
        {
            "ingredient_id": "thit_heo", "status": "fulfilled",
            "batches_used": [{"batch_id": "B1", "sku_id": "SKU-M001", "qty_taken_g": 500}],
        },
        {
            "ingredient_id": "hanh_la", "status": "skip",
            "batches_used": [],
        },
    ]
    sku_lookup = {
        "SKU-M001": {
            "retail_price": 85000, "cost_price": 68000, "pack_size_g": 500,
            "product_name": "Thịt heo", "category_l1": "fresh_meat",
        },
    }
    result = compute_bundle_prices(ingredient_status, sku_lookup)
    assert result["bundle_retail"] == 85000
    assert result["bundle_cost"] == 68000
    assert len(result["items"]) == 1  # skip excluded


def test_compute_weighted_min_margin():
    category_costs = {"fresh_meat": 68000, "fresh_produce": 12000}
    bundle_cost = 80000
    margins = {"fresh_meat": 0.12, "fresh_produce": 0.20}
    min_margin = compute_weighted_min_margin(category_costs, bundle_cost, margins)
    # (68000/80000)*0.12 + (12000/80000)*0.20 = 0.102 + 0.030 = 0.132
    assert abs(min_margin - 0.132) < 0.001


def test_apply_discount_within_margin():
    result = apply_discount(
        bundle_retail=100000, bundle_cost=60000,
        waste_score_normalized=0.5, min_margin=0.15,
    )
    # raw_discount = 0.05 + 0.25*0.5 = 0.175
    # discounted = 100000 * 0.825 = 82500
    # margin = (82500-60000)/82500 = 0.2727 >= 0.15 -> OK
    assert abs(result["discount_rate"] - 0.175) < 0.001
    assert abs(result["final_price"] - 82500) < 1


def test_apply_discount_margin_floor():
    result = apply_discount(
        bundle_retail=70000, bundle_cost=65000,
        waste_score_normalized=1.0, min_margin=0.15,
    )
    # raw_discount = 0.30
    # discounted = 70000 * 0.70 = 49000
    # margin = (49000-65000)/49000 < 0 -> falls back
    # final_price = 65000 / (1-0.15) = 76470.59 > bundle_retail
    # actual_discount = 1 - 76470.59/70000 < 0 -> clamped to 0
    assert result["discount_rate"] == 0
    assert result["gross_margin"] >= 0.15 - 0.001
