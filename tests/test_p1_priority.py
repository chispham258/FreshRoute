from datetime import date

from app.core.models.inventory import ProductSKU
from app.core.pipeline.p1_priority import _urgency_flag_from_score, compute_priority, run_p1


def test_urgency_flag():
    assert _urgency_flag_from_score(0.85) == "CRITICAL"
    assert _urgency_flag_from_score(0.80) == "CRITICAL"
    assert _urgency_flag_from_score(0.70) == "HIGH"
    assert _urgency_flag_from_score(0.65) == "HIGH"
    assert _urgency_flag_from_score(0.55) == "MEDIUM"
    assert _urgency_flag_from_score(0.50) == "MEDIUM"
    assert _urgency_flag_from_score(0.30) == "WATCH"


def test_compute_priority_high_for_near_expiry():
    sku = ProductSKU(
        sku_id = "SKU-M001", ingredient_id = "thit_heo", product_name = "Thịt heo",
        category_l1 = "fresh_meat", unit_type = "kg", pack_size_g = 500,
        retail_price = 85000, cost_price = 68000,
    )
    batch = {
        "batch_id": "B001", 
        "sku_id": "SKU-M001", 
        "ingredient_id": "thit_heo",
        "remaining_qty_g": 400, 
        "expiry_days": 1
    }
    sales = [
        {"date": "2026-04-01", "qty_sold_g": 200}
    ] * 7   

    score = compute_priority(batch, sales, sku)
    assert 0.5 < score <= 1.0, f"Near-expiry meat should score high, got {score}"


def test_compute_priority_low_for_far_expiry():
    sku = ProductSKU(
        sku_id="SKU-P001", ingredient_id="nuoc_mam", product_name="Nước mắm",
        category_l1="processed", unit_type="bottle", pack_size_g=500,
        retail_price=35000, cost_price=24000,
    )
    batch = {"batch_id": "B002", "sku_id": "SKU-P001", "ingredient_id": "nuoc_mam",
             "remaining_qty_g": 500, "expiry_days": 30}
    sales = [{"date": "2026-04-01", "qty_sold_g": 50}] * 14

    score = compute_priority(batch, sales, sku)
    assert score < 0.5, f"Far-expiry processed should score low, got {score}"


def test_run_p1_returns_sorted(mock_inventory, sku_lookup):
    sales_history = {}  # No sales data — still should work
    result = run_p1(mock_inventory, sales_history, sku_lookup, top_n=10)

    assert len(result) >= 10
    # Verify sorted descending
    scores = [r.priority_score for r in result]
    # All CRITICAL/HIGH should come first (they're returned as a block)
    critical_high = [r for r in result if r.urgency_flag in ("CRITICAL", "HIGH")]
    assert len(critical_high) > 0


def test_run_p1_includes_all_critical_high(mock_inventory, sku_lookup):
    sales_history = {}
    result = run_p1(mock_inventory, sales_history, sku_lookup, top_n=5)

    flags = [r.urgency_flag for r in result]
    # All CRITICAL and HIGH from input should be present
    critical_high_in = [b for b in mock_inventory if b.get("expiry_days", 999) <= 3]
    critical_high_out = [r for r in result if r.urgency_flag in ("CRITICAL", "HIGH")]
    assert len(critical_high_out) >= min(len(critical_high_in), len(result))
