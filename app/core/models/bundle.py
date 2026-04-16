from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class BatchUsed(BaseModel):
    batch_id: str
    sku_id: str
    qty_taken_g: float


class IngredientStatus(BaseModel):
    ingredient_id: str
    status: Literal["fulfilled", "substitute", "skip", "missing"]
    is_optional: bool
    substitute_id: Optional[str] = None
    batches_used: List[BatchUsed] = []
    urgency_flag: Optional[str] = None

    # NEW packet-based fields
    allocated_g: float = 0.0
    deviation: float = 0.0
    allocation_strategy: str = "none"  # "strict", "approx", or "none"


class BundleIngredientDisplay(BaseModel):
    ingredient_id: str
    sku_id: str
    product_name: str
    qty_taken_g: float
    item_retail_price: float
    is_substitute: bool
    substitute_id: Optional[str] = None
    urgency_flag: Optional[str] = None


class BundleOutput(BaseModel):
    bundle_id: str
    recipe_id: str
    recipe_name: str
    rank: int
    final_score: float
    urgency_coverage_score: float
    completeness_score: float
    waste_score_normalized: float
    original_price: float
    discount_rate: float
    final_price: float
    gross_profit: float
    gross_margin: float
    ingredients: List[BundleIngredientDisplay]
    has_substitute: bool
    store_id: str
    generated_at: datetime

    # NEW packet-based fields
    avg_deviation: float = 0.0
    total_rounding_loss_g: float = 0.0
    allocation_strategy: str = "none"


class BundleEvent(BaseModel):
    bundle_id: str
    recipe_id: str
    store_id: str
    event_type: Literal["impression", "click", "purchase", "skip"]
    user_id: Optional[str] = None
    rank_at_time: int
    final_score: float
    urgency_coverage_score: float
    completeness_score: float
    waste_score_normalized: float
