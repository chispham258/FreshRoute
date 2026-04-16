"""
app/engine/waste.py
Waste scoring engine. Shared by B2B pipeline (P5) and future B2C extensions.
"""

ALPHA = 0.3   # rounding loss penalty weight
BETA = 0.5    # deviation penalty weight


def compute_waste_score(
    rescued_value: float,
    rounding_loss_g: float,
    deviation: float,
) -> float:
    """
    Compute waste score for a bundle ingredient.

    waste_score = rescued_value
                - alpha * rounding_loss_g
                - beta * deviation

    Args:
        rescued_value: cost * urgency of allocated ingredients (fulfilled only)
        rounding_loss_g: over-allocated grams due to packet rounding
        deviation: fractional gap between allocated_g and required_g

    Returns:
        Waste score (higher is better)
    """
    return rescued_value - ALPHA * rounding_loss_g - BETA * deviation
