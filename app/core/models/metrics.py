from typing import Optional

from pydantic import BaseModel


class BundleMetrics(BaseModel):
    bundle_id: str
    recipe_id: str
    impressions: int
    clicks: int
    purchases: int
    skips: int
    ctr: float  # clicks / impressions
    cvr: float  # purchases / impressions


class StoreSummary(BaseModel):
    store_id: str
    date: str
    total_bundles: int
    total_impressions: int
    total_clicks: int
    total_purchases: int
    avg_ctr: float
    avg_cvr: float
    total_revenue: Optional[float] = None
    total_waste_saved: Optional[float] = None
