"""
P1 — Inventory Risk Scoring

INPUT:  List[dict] from StoreConnector.get_batches() + sales history
OUTPUT: List[P1Output] sorted by priority_score descending, top N
"""

import math
from typing import List, Optional

from app.core.models.inventory import P1Output, ProductSKU

# Decay lambda per category
LAMBDA_BY_CATEGORY = {
    "fresh_seafood": 0.60,
    "fresh_meat": 0.50,
    "fresh_produce": 0.25,
    "dairy": 0.12,
    "processed": 0.08,
}

# Component weights per category
WEIGHTS_BY_CATEGORY = {
    "fresh_meat":    {"w_e": 0.65, "w_s": 0.25, "w_d": 0.10},
    "fresh_seafood": {"w_e": 0.65, "w_s": 0.25, "w_d": 0.10},
    "fresh_produce": {"w_e": 0.55, "w_s": 0.30, "w_d": 0.15},
    "dairy":         {"w_e": 0.45, "w_s": 0.35, "w_d": 0.20},
    "processed":     {"w_e": 0.30, "w_s": 0.45, "w_d": 0.25},
}


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _urgency_flag_from_score(priority_score: float) -> str:
    """Determine urgency tier based on priority_score (0-1).

    This combines expiry urgency, sales velocity, and cost impact into a single
    urgency assessment. High-score items are strategically important to move.

    Thresholds:
    - CRITICAL: >= 0.80 (highest priority — move at any discount)
    - HIGH:     >= 0.65 (strong priority — aggressive discount)
    - MEDIUM:   >= 0.50 (moderate priority — standard discount)
    - WATCH:    < 0.50 (monitor — minimal action)
    """
    if priority_score >= 0.80:
        return "CRITICAL"
    elif priority_score >= 0.65:
        return "HIGH"
    elif priority_score >= 0.50:
        return "MEDIUM"
    else:
        return "WATCH"


def compute_priority(
    batch: dict,
    sales_history: Optional[List[dict]],
    sku: ProductSKU,
) -> float:
    """Compute priority score for a single batch."""
    category = sku.category_l1
    lam = LAMBDA_BY_CATEGORY.get(category, 0.25)
    weights = WEIGHTS_BY_CATEGORY.get(category, WEIGHTS_BY_CATEGORY["fresh_produce"])

    expiry_days = max(batch["expiry_days"], 0)

    # Expiry urgency component
    expiry_score = math.exp(-lam * expiry_days)

    # Supply/demand component
    if sales_history:
        non_zero_sales = [s["qty_sold_g"] for s in sales_history if s["qty_sold_g"] > 0]
        avg_daily_sales = sum(s["qty_sold_g"] for s in sales_history) / max(len(sales_history), 1)
        stockout_count = sum(1 for s in sales_history if s["qty_sold_g"] == 0)
    else:
        avg_daily_sales = 0
        stockout_count = 0

    if avg_daily_sales > 0:
        days_of_supply = batch["remaining_qty_g"] / avg_daily_sales
    else:
        days_of_supply = float("inf")

    supply_score = _sigmoid(days_of_supply / max(expiry_days, 1) - 1)

    # Demand weakness component
    if stockout_count == 0 and sales_history:
        total_available = batch["remaining_qty_g"]
        total_sold = sum(s["qty_sold_g"] for s in sales_history)
        sell_through_rate = total_sold / (total_sold + total_available) if (total_sold + total_available) > 0 else 0
        demand_score = 1 - sell_through_rate
    else:
        demand_score = 0

    priority = (
        weights["w_e"] * expiry_score
        + weights["w_s"] * supply_score
        + weights["w_d"] * demand_score
    )

    return min(max(priority, 0.0), 1.0)


def run_p1(
    batches: List[dict],
    sales_history: dict,
    sku_lookup: dict,
    top_n: int = 20,
) -> List[P1Output]:
    """
    Run P1 priority scoring on all batches.

    Args:
        batches: raw batches from StoreConnector
        sales_history: sku_id -> List[{date, qty_sold_g}]
        sku_lookup: sku_id -> ProductSKU
        top_n: minimum number of batches to return
    """
    scored = []
    for batch in batches:
        sku = sku_lookup.get(batch["sku_id"])
        if not sku:
            continue
        sales = sales_history.get(batch["sku_id"], [])
        score = compute_priority(batch, sales, sku)
        expiry_days = max(batch["expiry_days"], 0)

        scored.append(P1Output(
            batch_id=batch["batch_id"],
            sku_id=batch["sku_id"],
            ingredient_id=batch["ingredient_id"],
            priority_score=round(score, 6),
            expiry_days=expiry_days,
            remaining_qty_g=batch["remaining_qty_g"],
            urgency_flag=_urgency_flag_from_score(score),
        ))

    # Sort by priority descending
    scored.sort(key=lambda x: x.priority_score, reverse=True)

    # Return all CRITICAL + HIGH, plus enough MEDIUM to reach top_n
    critical_high = [s for s in scored if s.urgency_flag in ("CRITICAL", "HIGH")]
    if len(critical_high) >= top_n:
        return critical_high

    remaining = [s for s in scored if s.urgency_flag not in ("CRITICAL", "HIGH")]
    needed = max(top_n - len(critical_high), 0)
    return critical_high + remaining[:needed]
