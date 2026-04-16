from app.core.pipeline.p6_ranking import compute_final_score, compute_penalty, run_p6


def test_compute_penalty_no_substitutes():
    status = [
        {"ingredient_id": "a", "status": "fulfilled"},
        {"ingredient_id": "b", "status": "fulfilled"},
    ]
    assert compute_penalty(status) == 0.0


def test_compute_penalty_with_substitutes():
    status = [
        {"ingredient_id": "a", "status": "fulfilled"},
        {"ingredient_id": "b", "status": "substitute"},
        {"ingredient_id": "c", "status": "skip"},
    ]
    # skip excluded: 2 active, 1 substitute -> 0.05 * (1/2) = 0.025
    assert abs(compute_penalty(status) - 0.025) < 0.001


def test_compute_final_score():
    recipe = {
        "recipe_id": "R1",
        "urgency_coverage_score": 0.8,
        "completeness_score": 1.0,
        "waste_score_normalized": 0.7,
        "ingredient_status": [{"ingredient_id": "a", "status": "fulfilled"}],
    }
    weights = {"w1": 0.5, "w2": 0.3, "w3": 0.2, "w4": 0.0}
    score = compute_final_score(recipe, weights)
    expected = 0.5 * 0.8 + 0.3 * 1.0 + 0.2 * 0.7  # 0.4 + 0.3 + 0.14 = 0.84
    assert abs(score - expected) < 0.001


def test_run_p6_ranks():
    p5_output = [
        {
            "recipe_id": "R1", "urgency_coverage_score": 0.5, "completeness_score": 1.0,
            "waste_score_normalized": 0.3,
            "ingredient_status": [{"ingredient_id": "a", "status": "fulfilled"}],
        },
        {
            "recipe_id": "R2", "urgency_coverage_score": 0.9, "completeness_score": 1.0,
            "waste_score_normalized": 0.8,
            "ingredient_status": [{"ingredient_id": "a", "status": "fulfilled"}],
        },
    ]
    result = run_p6(p5_output, "STORE1", firestore_client=None, top_k=10)
    assert result[0]["recipe_id"] == "R2"  # higher score
    assert result[0]["rank"] == 1
    assert result[1]["rank"] == 2
