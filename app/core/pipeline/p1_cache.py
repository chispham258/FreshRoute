"""
P1 result cache — in-memory, TTL-based.

Stores P1Output scored batches per store so that /inventory can read
pre-computed scores without re-running the full pipeline.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from app.core.models.inventory import P1Output

_TTL_MINUTES = 60
_store: dict[str, Tuple[datetime, List[P1Output]]] = {}


def get(store_id: str) -> Optional[List[P1Output]]:
    entry = _store.get(store_id)
    if not entry:
        return None
    computed_at, scores = entry
    if datetime.now() - computed_at > timedelta(minutes=_TTL_MINUTES):
        return None
    return scores


def put(store_id: str, scores: List[P1Output]) -> None:
    _store[store_id] = (datetime.now(), scores)


def invalidate(store_id: str) -> None:
    """Drop cached P1 scores for one store (e.g. after batch data regeneration)."""
    _store.pop(store_id, None)


def clear_all() -> None:
    """Drop all cached P1 scores."""
    _store.clear()
