"""Tests for waste scoring engine."""

import pytest
from app.core.engine.waste import compute_waste_score, ALPHA, BETA


class TestWasteScoring:
    """Test waste score computation."""

    def test_no_penalty_on_exact_allocation(self):
        """Exact allocation should have no penalties."""
        score = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.0)
        assert score == 100.0

    def test_rounding_loss_reduces_score(self):
        """Rounding loss should reduce the waste score."""
        s1 = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.0)
        s2 = compute_waste_score(rescued_value=100.0, rounding_loss_g=500.0, deviation=0.0)
        penalty = ALPHA * 500.0
        assert s2 == s1 - penalty
        assert s2 < s1

    def test_deviation_reduces_score(self):
        """Allocation deviation should reduce the waste score."""
        s1 = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.0)
        s2 = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.2)
        penalty = BETA * 0.2
        assert s2 == s1 - penalty
        assert s2 < s1

    def test_both_penalties_applied(self):
        """Both rounding loss and deviation should reduce score."""
        s1 = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.0)
        s2 = compute_waste_score(rescued_value=100.0, rounding_loss_g=500.0, deviation=0.2)
        total_penalty = ALPHA * 500.0 + BETA * 0.2
        assert abs((s1 - total_penalty) - s2) < 0.01  # Use approximate equality for float comparison

    def test_rescued_value_weighted_more(self):
        """Rescued value should have more impact than penalties."""
        # High rescued value with some loss
        s1 = compute_waste_score(rescued_value=1000.0, rounding_loss_g=100.0, deviation=0.1)
        # Low rescued value with no loss
        s2 = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.0)
        # High value should still win despite some loss
        assert s1 > s2

    def test_zero_rescued_value(self):
        """Zero rescued value should not contribute to waste."""
        s1 = compute_waste_score(rescued_value=0.0, rounding_loss_g=0.0, deviation=0.0)
        s2 = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.0)
        assert s1 < s2


class TestWastePenaltyWeights:
    """Test the penalty weight constants."""

    def test_alpha_weight_for_rounding_loss(self):
        """Verify ALPHA weight for rounding loss penalty."""
        # ALPHA = 0.3, so 1g of rounding loss = 0.3 points
        assert ALPHA == 0.3
        s = compute_waste_score(rescued_value=100.0, rounding_loss_g=1.0, deviation=0.0)
        assert s == 100.0 - 0.3

    def test_beta_weight_for_deviation(self):
        """Verify BETA weight for deviation penalty."""
        # BETA = 0.5, so 0.01 deviation = 0.005 points
        assert BETA == 0.5
        s = compute_waste_score(rescued_value=100.0, rounding_loss_g=0.0, deviation=0.01)
        assert s == 100.0 - 0.005

    def test_weights_are_reasonable(self):
        """Weights should balance rescued value with penalties."""
        # High rounding loss of 1000g should reduce score by ALPHA * 1000 = 300
        # But can still be positive if rescued value is high enough
        s = compute_waste_score(rescued_value=500.0, rounding_loss_g=1000.0, deviation=0.0)
        assert s == 500.0 - 300.0
        assert s == 200.0  # Still positive, making high waste reduction valuable


class TestWasteScoreRanges:
    """Test realistic waste score ranges."""

    def test_small_waste_reduction(self):
        """Score for rescuing small cost items."""
        # Rescue 200g of item worth 50 VND/g
        score = compute_waste_score(rescued_value=10000.0, rounding_loss_g=0.0, deviation=0.0)
        assert score == 10000.0

    def test_large_waste_reduction(self):
        """Score for rescuing expensive items."""
        # Rescue 1kg of item worth 150 VND/g = 150k VND value
        score = compute_waste_score(rescued_value=150000.0, rounding_loss_g=0.0, deviation=0.0)
        assert score == 150000.0

    def test_score_can_go_negative(self):
        """Score can be negative if penalties exceed value."""
        # Small rescued value but large penalties
        score = compute_waste_score(rescued_value=10.0, rounding_loss_g=1000.0, deviation=1.0)
        penalty = ALPHA * 1000.0 + BETA * 1.0
        assert score == 10.0 - penalty
        assert score < 0  # Negative score possible

    def test_realistic_bundle_score(self):
        """Score for a realistic bundle."""
        # Rescue 5 kg of meat (cost 80k, pack_size 500g = 160k per batch)
        # Plus 2 kg of produce (cost 20k, pack_size 300g = 40k per batch)
        # Total rescued: 200k with some rounding loss and deviation
        rescued = 200000.0
        rounding_loss = 200.0  # Over-allocated 200g
        deviation = 0.1  # 10% deviation
        score = compute_waste_score(rescued, rounding_loss, deviation)
        penalty = ALPHA * 200.0 + BETA * 0.1
        assert score == rescued - penalty
        assert score > 0  # Still positive
