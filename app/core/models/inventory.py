from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class ProductSKU(BaseModel):
    sku_id: str
    ingredient_id: str
    product_name: str
    category_l1: Literal["fresh_meat", "fresh_seafood", "fresh_produce", "dairy", "processed"]
    category_l2: Optional[str] = None
    unit_type: Literal["kg", "piece", "pack", "bottle", "bag"]
    pack_size_g: float = 500.0       # canonical pack size per SKU
    retail_price: float
    cost_price: float
    typical_shelf_life_days: Optional[int] = None


class ProductBatch(BaseModel):
    batch_id: str
    sku_id: str
    ingredient_id: str
    store_id: str

    unit_count: int          # number of discrete packets in stock
    pack_size_g: float       # grams per individual packet

    expiry_date: date
    expiry_days: int

    received_at: datetime = None
    cost_price: float

    @property
    def total_quantity_g(self) -> float:
        """Derived property: always computed from unit_count * pack_size_g"""
        return self.unit_count * self.pack_size_g

    @classmethod
    def from_legacy(cls, data: dict, pack_size_g: float) -> "ProductBatch":
        """Migrate old remaining_qty_g batches to packet-based model."""
        if "remaining_qty_g" in data and "unit_count" not in data:
            data = {**data}
            data["unit_count"] = max(1, round(data.pop("remaining_qty_g") / pack_size_g))
        return cls(**data)


class P1Output(BaseModel):
    batch_id: str
    sku_id: str
    ingredient_id: str
    priority_score: float
    expiry_days: int
    remaining_qty_g: float
    urgency_flag: Literal["CRITICAL", "HIGH", "MEDIUM", "WATCH"]
