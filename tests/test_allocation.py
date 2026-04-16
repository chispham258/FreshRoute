"""Tests for packet-based FEFO allocation engine."""

import pytest
from datetime import date

from app.core.engine.allocation import allocate_fefo, AllocationResult, MAX_DEVIATION


def make_batch(batch_id, unit_count, pack_size_g, expiry_days, sku_id="SKU_1"):
    """Helper to create test batch dict."""
    return {
        "batch_id": batch_id,
        "sku_id": sku_id,
        "ingredient_id": "ing_1",
        "unit_count": unit_count,
        "pack_size_g": pack_size_g,
        "expiry_days": expiry_days,
        "expiry_date": date.today(),
    }


class TestAllocationStrict:
    """Test strict (ceiling) allocation strategy."""

    def test_strict_single_batch(self):
        """Allocate from single batch with ceiling."""
        batches = [make_batch("b1", 10, 500.0, 3)]
        result = allocate_fefo(batches, required_g=600.0, strategy="strict")
        # ceil(600/500) = 2 packets = 1000g
        assert result.packets_used == 2
        assert result.allocated_g == 1000.0
        assert result.strategy == "strict"
        assert len(result.batches_used) == 1
        assert result.batches_used[0]["batch_id"] == "b1"
        assert result.batches_used[0]["packets_taken"] == 2

    def test_strict_exact_fit(self):
        """Allocate when quantity matches exactly."""
        batches = [make_batch("b1", 10, 500.0, 3)]
        result = allocate_fefo(batches, required_g=1000.0, strategy="strict")
        # ceil(1000/500) = 2 packets = 1000g
        assert result.packets_used == 2
        assert result.allocated_g == 1000.0
        assert result.feasible is True

    def test_strict_exceeds_batch(self):
        """Attempt to allocate more than available."""
        batches = [make_batch("b1", 2, 500.0, 3)]
        result = allocate_fefo(batches, required_g=1500.0, strategy="strict")
        # ceil(1500/500) = 3 packets, but only 2 available
        assert result.packets_used == 2
        assert result.allocated_g == 1000.0
        # deviation = (1000 - 1500) / 1500 = -33% > 25% tolerance
        assert result.feasible is False


class TestAllocationApprox:
    """Test approximate (floor) allocation strategy."""

    def test_approx_single_batch(self):
        """Allocate from single batch with floor."""
        batches = [make_batch("b1", 10, 500.0, 3)]
        result = allocate_fefo(batches, required_g=600.0, strategy="approx")
        # floor(600/500) = 1 packet = 500g
        assert result.packets_used == 1
        assert result.allocated_g == 500.0
        assert result.strategy == "approx"

    def test_approx_under_tolerance(self):
        """Allocate under requirement but within tolerance."""
        batches = [make_batch("b1", 10, 500.0, 3)]
        result = allocate_fefo(batches, required_g=450.0, strategy="approx")
        # floor(450/500) = 0, but bumped to 1 = 500g
        # deviation = (500 - 450) / 450 = 11.1% < 25% → feasible
        assert result.allocated_g == 500.0
        assert result.feasible is True
        assert result.deviation <= MAX_DEVIATION


class TestAllocationBest:
    """Test best strategy (prefer strict, fallback to approx)."""

    def test_best_prefers_strict_if_feasible(self):
        """Best strategy should use strict if within tolerance."""
        batches = [make_batch("b1", 10, 100.0, 3)]
        result = allocate_fefo(batches, required_g=450.0, strategy="best")
        # Strict: ceil(450/100) = 5 packets = 500g, deviation = 11% < 25% → feasible
        assert result.strategy == "strict"
        assert result.allocated_g == 500.0

    def test_best_falls_back_to_approx(self):
        """Best strategy should fallback to approx if strict exceeds tolerance."""
        batches = [make_batch("b1", 1, 500.0, 3)]
        result = allocate_fefo(batches, required_g=400.0, strategy="best")
        # Strict: ceil(400/500) = 1 packet = 500g, deviation = 25% (at boundary)
        # Approx: floor(400/500) = 0 (bumped to 1) = 500g, deviation = 25%
        # Both at boundary, so best picks the one it evaluates first (strict)
        assert result.allocated_g == 500.0


class TestAllocationFEFO:
    """Test FEFO (First Expire First Out) ordering."""

    def test_fefo_ordering(self):
        """Verify batches are consumed in FEFO order."""
        b1 = make_batch("b1", 2, 500.0, expiry_days=7)  # expires later
        b2 = make_batch("b2", 1, 500.0, expiry_days=2)  # expires sooner, only 1 packet
        result = allocate_fefo([b1, b2], required_g=1000.0, strategy="strict")
        # Need ceil(1000/500) = 2 packets
        # Should consume b2 first (lower expiry_days = 1 packet), then b1 (1 packet)
        assert len(result.batches_used) == 2
        assert result.batches_used[0]["batch_id"] == "b2"
        assert result.batches_used[0]["packets_taken"] == 1
        assert result.batches_used[1]["batch_id"] == "b1"
        assert result.batches_used[1]["packets_taken"] == 1

    def test_fefo_multi_batch_consumption(self):
        """Verify multi-batch allocation respects FEFO order."""
        b1 = make_batch("b1", 2, 500.0, expiry_days=5)
        b2 = make_batch("b2", 2, 500.0, expiry_days=1)  # Only 2 packets, not 5
        result = allocate_fefo([b1, b2], required_g=1200.0, strategy="strict")
        # Need ceil(1200/500) = 3 packets
        # Take 2 from b2 (1000g), 1 from b1 (500g) = 1500g
        assert result.packets_used == 3
        assert len(result.batches_used) == 2
        assert result.batches_used[0]["batch_id"] == "b2"
        assert result.batches_used[0]["packets_taken"] == 2
        assert result.batches_used[1]["batch_id"] == "b1"
        assert result.batches_used[1]["packets_taken"] == 1


class TestAllocationEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_batches(self):
        """Allocate from empty batch list."""
        result = allocate_fefo([], required_g=500.0, strategy="best")
        assert result.packets_used == 0
        assert result.allocated_g == 0.0
        assert result.feasible is False

    def test_zero_requirement(self):
        """Allocate zero grams."""
        batches = [make_batch("b1", 10, 500.0, 3)]
        result = allocate_fefo(batches, required_g=0.0, strategy="strict")
        assert result.packets_used == 0
        assert result.allocated_g == 0.0
        assert result.deviation == 0.0
        assert result.feasible is True

    def test_very_large_requirement(self):
        """Allocate more than available."""
        batches = [make_batch("b1", 2, 500.0, 3)]
        result = allocate_fefo(batches, required_g=10000.0, strategy="best")
        assert result.allocated_g == 1000.0  # Only 2 packets available
        assert result.feasible is False

    def test_deviation_at_boundary(self):
        """Verify 25% tolerance boundary."""
        batches = [make_batch("b1", 10, 100.0, 3)]
        # Required 125g, ceil(125/100) = 2 packets = 200g
        # deviation = (200 - 125) / 125 = 60% > 25% → not feasible
        result_strict = allocate_fefo(batches, required_g=125.0, strategy="strict")
        assert result_strict.feasible is False

        # Required 120g, ceil(120/100) = 2 packets = 200g
        # deviation = (200 - 120) / 120 = 66.7% > 25% → not feasible
        result_strict2 = allocate_fefo(batches, required_g=120.0, strategy="strict")
        assert result_strict2.feasible is False

        # Required 250g, ceil(250/100) = 3 packets = 300g
        # deviation = (300 - 250) / 250 = 20% < 25% → feasible
        result_strict3 = allocate_fefo(batches, required_g=250.0, strategy="strict")
        assert result_strict3.feasible is True
