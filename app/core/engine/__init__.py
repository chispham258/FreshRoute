# app/engine/__init__.py
from .allocation import allocate_fefo, AllocationResult, MAX_DEVIATION
from .waste import compute_waste_score

__all__ = [
    "allocate_fefo",
    "AllocationResult",
    "MAX_DEVIATION",
    "compute_waste_score",
]
