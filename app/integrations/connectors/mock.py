import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List

from app.integrations.connectors.base import StoreConnector
from app.core.models.inventory import ProductBatch

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "tests" / "fixtures"


class MockConnector(StoreConnector):
    """Returns mock data from fixture files for hackathon demo."""

    def __init__(self):
        self._batches_cache: dict[str, List[dict]] = {}
        self._skus_cache: dict[str, dict] = {}

    def _load_fixtures(self):
        if self._batches_cache:
            return
        with open(FIXTURES_DIR / "batches.json", encoding="utf-8") as f:
            all_batches = json.load(f)
        for b in all_batches:
            store = b["store_id"]
            self._batches_cache.setdefault(store, []).append(b)
        with open(FIXTURES_DIR / "skus.json", encoding="utf-8") as f:
            skus = json.load(f)
        for s in skus:
            self._skus_cache[s["sku_id"]] = s

    def get_batches(self, store_id: str) -> List[ProductBatch]:
        self._load_fixtures()
        batches = self._batches_cache.get(store_id, [])
        # If the requested store_id doesn't exist in fixtures (tests may pass
        # synthetic IDs), fall back to returning all batches across stores so
        # the caller can still exercise allocation and pipeline logic.
        if not batches:
            # flatten all batches
            batches = [b for store_batches in self._batches_cache.values() for b in store_batches]
        today = date.today()
        result = []
        for b in batches:
            exp = date.fromisoformat(b["expiry_date"]) if isinstance(b["expiry_date"], str) else b["expiry_date"]

            # Get pack_size_g from batch or SKU
            if "pack_size_g" in b:
                pack_size_g = b["pack_size_g"]
            else:
                sku = self._skus_cache.get(b["sku_id"])
                pack_size_g = sku.get("pack_size_g", 500.0) if sku else 500.0

            # Compute remaining_qty_g for compatibility
            if "remaining_qty_g" in b:
                remaining = b["remaining_qty_g"]
            elif "unit_count" in b:
                remaining = b["unit_count"] * pack_size_g
            else:
                remaining = 0

            if remaining <= 0:
                continue

            # Build batch data
            batch_data = {
                "batch_id": b["batch_id"],
                "sku_id": b["sku_id"],
                "ingredient_id": b["ingredient_id"],
                "store_id": store_id,
                "expiry_date": exp,
                "expiry_days": (exp - today).days,
                "received_at": b.get("received_at", datetime.now().isoformat()),
                "cost_price": b.get("cost_price", 0),
            }

            # Add unit_count and pack_size_g
            if "unit_count" in b:
                batch_data["unit_count"] = b["unit_count"]
                batch_data["pack_size_g"] = pack_size_g
                result.append(ProductBatch(**batch_data))
            else:
                # Legacy mode: use from_legacy
                batch_data["remaining_qty_g"] = remaining
                result.append(ProductBatch.from_legacy(batch_data, pack_size_g))

        return result

    def get_sales_history(self, store_id: str, sku_id: str, days: int = 14) -> List[dict]:
        self._load_fixtures()
        sku = self._skus_cache.get(sku_id)
        if not sku:
            return []
        # Generate realistic mock sales with variance
        base_daily = sku.get("pack_size_g", 500) * random.uniform(0.5, 2.0)
        today = date.today()
        history = []
        for i in range(days):
            d = today - timedelta(days=i + 1)
            # 10% chance of stockout day
            if random.random() < 0.10:
                qty = 0.0
            else:
                qty = base_daily * random.uniform(0.3, 1.8)
            history.append({"date": d.isoformat(), "qty_sold_g": round(qty, 2)})
        return history
