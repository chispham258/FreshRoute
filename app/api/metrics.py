from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.db.postgres import get_db_session
from app.core.pipeline.p8_tracking import aggregate_metrics, store_summary

router = APIRouter()


@router.get("/metrics/{store_id}")
async def get_metrics(
    store_id: str,
    date_str: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Returns BundleMetrics + StoreSummary for manager dashboard."""
    if not date_str:
        date_str = date.today().isoformat()

    summary = await store_summary(store_id, date_str, db_session)
    metrics = await aggregate_metrics(store_id, date_str, db_session)

    return {
        "summary": summary.model_dump(),
        "bundles": [m.model_dump() for m in metrics],
    }
