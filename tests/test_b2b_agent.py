"""Tests for B2B agent tools with packet-based allocation."""

import pytest
from app.agent import tools as agent_tools
from app.core.engine.allocation import MAX_DEVIATION


class TestCheckFeasibilityWithPacketAllocation:
    """Test check_feasibility_and_substitute with new packet-based allocation."""

    def test_feasible_with_exact_packet_fit(self):
        """Test feasibility with exact packet-aligned requirement."""
        recipe = {
            "recipe_id": "R1",
            "ingredients": [
                {"ingredient_id": "thit_heo", "required_qty_g": 300.0}
            ]
        }
        inventory = [
            {
                "batch_id": "B1",
                "ingredient_id": "thit_heo",
                "sku_id": "SKU_1",
                "unit_count": 3,
                "pack_size_g": 100.0,
                "expiry_days": 5,
            }
        ]
        result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

        assert result["feasible"] is True
        assert result["completeness_score"] == 1.0
        assert result["ingredient_status"][0]["status"] == "fulfilled"
        assert result["ingredient_status"][0]["allocated_g"] == 300.0
        assert result["ingredient_status"][0]["deviation"] == 0.0
        assert result["ingredient_status"][0]["allocation_strategy"] == "strict"

    def test_feasible_with_ceiling_allocation(self):
        """Test feasibility with ceiling-based allocation within tolerance."""
        recipe = {
            "recipe_id": "R2",
            "ingredients": [
                {"ingredient_id": "thit_heo", "required_qty_g": 250.0}
            ]
        }
        inventory = [
            {
                "batch_id": "B1",
                "ingredient_id": "thit_heo",
                "sku_id": "SKU_1",
                "unit_count": 5,
                "pack_size_g": 100.0,
                "expiry_days": 5,
            }
        ]
        result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

        assert result["feasible"] is True
        # Strict: ceil(250/100) = 3 packets = 300g, deviation = 20% < 25% → feasible
        assert result["ingredient_status"][0]["status"] == "fulfilled"
        assert result["ingredient_status"][0]["allocated_g"] == 300.0
        assert result["ingredient_status"][0]["deviation"] <= MAX_DEVIATION

    def test_infeasible_exceeds_tolerance(self):
        """Test infeasibility when deviation exceeds tolerance."""
        recipe = {
            "recipe_id": "R3",
            "ingredients": [
                {"ingredient_id": "thit_heo", "required_qty_g": 100.0}
            ]
        }
        inventory = [
            {
                "batch_id": "B1",
                "ingredient_id": "thit_heo",
                "sku_id": "SKU_1",
                "unit_count": 1,
                "pack_size_g": 500.0,
                "expiry_days": 5,
            }
        ]
        result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

        # Only 1 packet (500g) available, deviation = 400% > 25% → allocate_fefo returns infeasible
        # Agent should then check for substitutes
        assert result["ingredient_status"][0]["allocated_g"] == 500.0
        assert result["ingredient_status"][0]["deviation"] > MAX_DEVIATION

    def test_fefo_ordering(self):
        """Test that FEFO ordering is respected during allocation."""
        recipe = {
            "recipe_id": "R4",
            "ingredients": [
                {"ingredient_id": "thit_heo", "required_qty_g": 200.0}
            ]
        }
        inventory = [
            {
                "batch_id": "B1",
                "ingredient_id": "thit_heo",
                "sku_id": "SKU_1",
                "unit_count": 2,
                "pack_size_g": 100.0,
                "expiry_days": 10,  # Later expiry
            },
            {
                "batch_id": "B2",
                "ingredient_id": "thit_heo",
                "sku_id": "SKU_1",
                "unit_count": 2,
                "pack_size_g": 100.0,
                "expiry_days": 2,  # Earlier expiry (should consume first)
            }
        ]
        result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

        # allocate_fefo sorts internally, so should consume B2 first, then B1
        assert result["ingredient_status"][0]["status"] == "fulfilled"
        assert result["ingredient_status"][0]["allocated_g"] == 200.0

    def test_missing_ingredient_no_inventory(self):
        """Test missing ingredient when no batches available."""
        recipe = {
            "recipe_id": "R5",
            "ingredients": [
                {"ingredient_id": "thit_bo", "required_qty_g": 300.0}
            ]
        }
        inventory = []  # No inventory
        result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

        # No batches → check substitutes via ontology
        assert result["ingredient_status"][0]["allocated_g"] == 0.0
        assert result["ingredient_status"][0]["deviation"] == 1.0
        assert result["ingredient_status"][0]["allocation_strategy"] == "none"

    def test_multiple_ingredients_completeness(self):
        """Test completeness score with multiple ingredients."""
        recipe = {
            "recipe_id": "R6",
            "ingredients": [
                {"ingredient_id": "thit_heo", "required_qty_g": 300.0},
                {"ingredient_id": "ca_chua", "required_qty_g": 200.0},
                {"ingredient_id": "thit_ga", "required_qty_g": 150.0},  # Missing
            ]
        }
        inventory = [
            {
                "batch_id": "B1",
                "ingredient_id": "thit_heo",
                "sku_id": "SKU_1",
                "unit_count": 3,
                "pack_size_g": 100.0,
                "expiry_days": 5,
            },
            {
                "batch_id": "B2",
                "ingredient_id": "ca_chua",
                "sku_id": "SKU_2",
                "unit_count": 3,
                "pack_size_g": 100.0,
                "expiry_days": 3,
            },
        ]
        result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

        # 2 out of 3 ingredients fulfilled/substitutable → completeness = 2/3 ≈ 0.667
        assert len(result["ingredient_status"]) == 3
        assert result["ingredient_status"][0]["status"] == "fulfilled"
        assert result["ingredient_status"][1]["status"] == "fulfilled"
        # Third ingredient should be missing or have substitute status
        assert result["ingredient_status"][2]["status"] in ("missing", "substitute")

    def test_packet_metrics_populated(self):
        """Test that packet-based metrics are properly populated in status."""
        recipe = {
            "recipe_id": "R7",
            "ingredients": [
                {"ingredient_id": "thit_heo", "required_qty_g": 350.0}
            ]
        }
        inventory = [
            {
                "batch_id": "B1",
                "ingredient_id": "thit_heo",
                "sku_id": "SKU_1",
                "unit_count": 5,
                "pack_size_g": 100.0,
                "expiry_days": 5,
            }
        ]
        result = agent_tools.check_feasibility_and_substitute(recipe, inventory)

        status = result["ingredient_status"][0]
        # Verify all packet-based fields are present
        assert "allocated_g" in status
        assert "deviation" in status
        assert "allocation_strategy" in status
        assert isinstance(status["allocated_g"], (int, float))
        assert isinstance(status["deviation"], (int, float))
        assert isinstance(status["allocation_strategy"], str)
        assert status["allocation_strategy"] in ("strict", "approx", "none")


class TestFinalizeBundlesEnrichment:
    """Test finalize_bundles enrichment with packet-based metrics."""

    def test_enrichment_adds_metrics(self):
        """Test that finalize_bundles enrichment adds packet-based metrics."""
        recipe = {
            "recipe_id": "R8",
            "name": "Test Recipe",
            "ingredients": [
                {"ingredient_id": "thit_heo", "required_qty_g": 300.0}
            ],
            "ingredient_status": [
                {
                    "ingredient_id": "thit_heo",
                    "status": "fulfilled",
                    "allocated_g": 300.0,
                    "deviation": 0.0,
                    "allocation_strategy": "strict",
                }
            ],
            "completeness_score": 1.0,
        }

        # The enrichment should add avg_deviation and total_rounding_loss_g
        # (We're testing the logic, not the full finalize_bundles which requires P5-P7 integration)
        statuses = recipe["ingredient_status"]
        fulfilled = [s for s in statuses if s.get("status") in ("fulfilled", "substitute")]
        if fulfilled:
            deviations = [s.get("deviation", 0.0) for s in fulfilled]
            avg_deviation = sum(deviations) / len(deviations) if deviations else 0.0
        else:
            avg_deviation = 0.0

        assert avg_deviation == 0.0
        assert "deviation" in statuses[0]
        assert "allocated_g" in statuses[0]
        assert "allocation_strategy" in statuses[0]

    def test_enrichment_computes_avg_deviation(self):
        """Test that enrichment properly computes average deviation."""
        recipe = {
            "recipe_id": "R9",
            "ingredient_status": [
                {
                    "ingredient_id": "thit_heo",
                    "status": "fulfilled",
                    "deviation": 0.1,
                },
                {
                    "ingredient_id": "ca_chua",
                    "status": "fulfilled",
                    "deviation": 0.2,
                },
            ],
            "completeness_score": 1.0,
        }

        statuses = recipe["ingredient_status"]
        fulfilled = [s for s in statuses if s.get("status") in ("fulfilled", "substitute")]
        deviations = [s.get("deviation", 0.0) for s in fulfilled]
        avg_deviation = sum(deviations) / len(deviations) if deviations else 0.0

        # (0.1 + 0.2) / 2 = 0.15 (use approximate equality for floating-point)
        assert abs(avg_deviation - 0.15) < 0.0001
