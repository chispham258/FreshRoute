"""End-to-end integration test: run full pipeline with mock data."""

import json
from pathlib import Path

import pytest

from app.integrations.connectors.mock import MockConnector
from app.core.models.inventory import ProductSKU
from app.core.pipeline.orchestrator import run_pipeline


@pytest.mark.asyncio
async def test_full_pipeline():
    connector = MockConnector()
    store_id = "BHX-HCM123"

    bundles = await run_pipeline(
        store_id=store_id,
        connector=connector,
        firestore_client=None,
        force_refresh=True,
        top_k_p6=10,
    )

    assert len(bundles) > 0
    assert len(bundles) <= 10

    for b in bundles:
        # Basic structure
        assert b.bundle_id.startswith("R")
        assert b.store_id == store_id
        assert b.rank >= 1

        # Scores
        assert b.final_score > 0
        assert b.urgency_coverage_score > 0
        assert 0 <= b.completeness_score <= 1.3  # can exceed 1.0 with optionals
        assert 0 <= b.waste_score_normalized <= 1.0

        # Pricing
        assert b.original_price > 0
        assert b.final_price > 0
        assert b.final_price <= b.original_price
        assert b.gross_margin >= 0
        assert 0 <= b.discount_rate <= 0.30

        # Ingredients
        assert len(b.ingredients) > 0

    # Ranks should be sequential
    ranks = [b.rank for b in bundles]
    assert ranks == list(range(1, len(bundles) + 1))

    # Scores should be descending
    scores = [b.final_score for b in bundles]
    assert scores == sorted(scores, reverse=True)

    print(f"\nPipeline produced {len(bundles)} bundles:")
    for b in bundles:
        print(f"  #{b.rank} {b.recipe_name}: {b.final_price:,.0f}đ "
              f"(-{b.discount_rate*100:.0f}%) margin={b.gross_margin*100:.1f}% "
              f"score={b.final_score:.3f}")
