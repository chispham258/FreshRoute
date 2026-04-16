from app.core.models.inventory import P1Output
from app.core.pipeline.p2_retrieval import (
    build_urgent_set,
    compute_urgency_coverage_score,
    run_p2,
)


def _make_p1(ingredient_id, priority, batch_id="B1"):
    return P1Output(
        batch_id=batch_id, sku_id="SKU-001", ingredient_id=ingredient_id,
        priority_score=priority, expiry_days=1, remaining_qty_g=500,
        urgency_flag="CRITICAL",
    )


def test_build_urgent_set():
    p1 = [_make_p1("thit_heo", 0.9, "B1"), _make_p1("thit_heo", 0.7, "B2"), _make_p1("ca_chua", 0.6, "B3")]
    urgent = build_urgent_set(p1)
    assert len(urgent["thit_heo"]) == 2
    assert len(urgent["ca_chua"]) == 1


def test_urgency_coverage_score_single():
    p1 = [_make_p1("thit_heo", 0.9)]
    urgent = build_urgent_set(p1)
    score = compute_urgency_coverage_score(["thit_heo"], urgent)
    assert abs(score - 0.9) < 0.001


def test_urgency_coverage_score_multiple():
    p1 = [_make_p1("thit_heo", 0.9, "B1"), _make_p1("ca_chua", 0.6, "B2")]
    urgent = build_urgent_set(p1)
    score = compute_urgency_coverage_score(["thit_heo", "ca_chua"], urgent)
    # max(0.9, 0.6) + 0.3 * min(0.9, 0.6) = 0.9 + 0.18 = 1.08
    assert abs(score - 1.08) < 0.001


def test_run_p2_returns_candidates(mock_inventory, sku_lookup, inverted_index, mock_recipes):
    from app.core.pipeline.p1_priority import run_p1

    p1_output = run_p1(mock_inventory, {}, sku_lookup, top_n=20)
    recipe_lookup = {r["recipe_id"]: r for r in mock_recipes}
    result = run_p2(p1_output, inverted_index, recipe_lookup, top_k=20)

    assert len(result) > 0
    assert all("urgency_coverage_score" in r for r in result)
    # Sorted descending
    scores = [r["urgency_coverage_score"] for r in result]
    assert scores == sorted(scores, reverse=True)
