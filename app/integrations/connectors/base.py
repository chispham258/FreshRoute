from abc import ABC, abstractmethod
from typing import List


class StoreConnector(ABC):
    """
    Abstract interface for connecting to any store POS/ERP database.
    Each store implementation only needs to implement these 2 methods.
    """

    @abstractmethod
    def get_batches(self, store_id: str) -> List[dict]:
        """
        Returns all active batches in store inventory.
        Normalized to ProductBatch-compatible format.
        Filter out: batches with remaining_qty_g <= 0.
        """
        pass

    @abstractmethod
    def get_sales_history(self, store_id: str, sku_id: str, days: int = 14) -> List[dict]:
        """
        Returns daily sales for a SKU over the past N days.
        [{"date": date, "qty_sold_g": float}]
        """
        pass
