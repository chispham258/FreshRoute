"""
P8 — Event Tracking and Metrics (MVP: tracking only, no weight updates)
"""

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.bundle import BundleEvent, BundleOutput
from app.core.models.metrics import BundleMetrics, StoreSummary


async def log_event(event: BundleEvent, db_session: AsyncSession) -> None:
    """Append-only insert to bundle_events. Fire-and-forget."""
    await db_session.execute(
        text("""
            INSERT INTO bundle_events
                (bundle_id, recipe_id, store_id, event_type, user_id,
                 rank_at_time, final_score, urgency_coverage_score,
                 completeness_score, waste_score_normalized)
            VALUES
                (:bundle_id, :recipe_id, :store_id, :event_type, :user_id,
                 :rank_at_time, :final_score, :urgency_coverage_score,
                 :completeness_score, :waste_score_normalized)
        """),
        event.model_dump(),
    )
    await db_session.commit()


async def aggregate_metrics(
    store_id: str,
    date_str: str,
    db_session: AsyncSession,
) -> List[BundleMetrics]:
    """Compute CTR/CVR per bundle for a given store and date."""
    result = await db_session.execute(
        text("""
            SELECT
                bundle_id,
                recipe_id,
                COUNT(*) FILTER (WHERE event_type = 'impression') as impressions,
                COUNT(*) FILTER (WHERE event_type = 'click') as clicks,
                COUNT(*) FILTER (WHERE event_type = 'purchase') as purchases,
                COUNT(*) FILTER (WHERE event_type = 'skip') as skips
            FROM bundle_events
            WHERE store_id = :store_id AND DATE(timestamp) = :date
            GROUP BY bundle_id, recipe_id
        """),
        {"store_id": store_id, "date": date_str},
    )

    metrics = []
    for row in result.mappings():
        impressions = row["impressions"] or 0
        clicks = row["clicks"] or 0
        purchases = row["purchases"] or 0
        skips = row["skips"] or 0

        metrics.append(BundleMetrics(
            bundle_id=row["bundle_id"],
            recipe_id=row["recipe_id"],
            impressions=impressions,
            clicks=clicks,
            purchases=purchases,
            skips=skips,
            ctr=clicks / impressions if impressions > 0 else 0,
            cvr=purchases / impressions if impressions > 0 else 0,
        ))

    return metrics


async def store_summary(
    store_id: str,
    date_str: str,
    db_session: AsyncSession,
) -> StoreSummary:
    """Aggregate store-level metrics."""
    metrics = await aggregate_metrics(store_id, date_str, db_session)

    total_impressions = sum(m.impressions for m in metrics)
    total_clicks = sum(m.clicks for m in metrics)
    total_purchases = sum(m.purchases for m in metrics)

    return StoreSummary(
        store_id=store_id,
        date=date_str,
        total_bundles=len(metrics),
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_purchases=total_purchases,
        avg_ctr=total_clicks / total_impressions if total_impressions > 0 else 0,
        avg_cvr=total_purchases / total_impressions if total_impressions > 0 else 0,
    )
