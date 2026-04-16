import logging
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from app.integrations.connectors.base import StoreConnector
from app.dependencies import get_connector, get_firestore
from app.core.models.bundle import BundleOutput
from app.core.pipeline.orchestrator import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory bundle cache: store_id → {bundles, generated_at}
# Refreshed by background task or force_refresh=True.
# TTL of 6 hours — enough for a typical retail day shift.
# ---------------------------------------------------------------------------
_CACHE_TTL = timedelta(hours=6)
_bundle_cache: dict[str, dict] = {}


def _cache_valid(store_id: str) -> bool:
    entry = _bundle_cache.get(store_id)
    if not entry:
        return False
    return datetime.now() - entry["generated_at"] < _CACHE_TTL


async def _refresh_cache(store_id: str, connector: StoreConnector, firestore_client):
    """Run the pipeline and populate the cache. Called as a background task."""
    logger.info(f"Background refresh task started for {store_id}")
    try:
        bundles = await run_pipeline(
            store_id=store_id,
            connector=connector,
            firestore_client=firestore_client,
            top_n=20,
            top_k_p2=20,
            top_k_p6=10,
        )
        _bundle_cache[store_id] = {
            "bundles": bundles,
            "generated_at": datetime.now(),
        }
        logger.info(f"Background refresh completed for {store_id}: {len(bundles)} bundles cached")
    except Exception as e:
        logger.error(f"Background bundle refresh failed for {store_id}: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/bundles/{store_id}", response_model=List[BundleOutput])
async def get_bundles(
    store_id: str,
    background_tasks: BackgroundTasks,
    force_refresh: bool = False,
    limit: int = 10,
    agent: bool = False,
    connector: StoreConnector = Depends(get_connector),
):
    """
    Returns top-K bundle recommendations for a store.

    - Default: deterministic P1-P7 pipeline with 6-hour cache.
    - ?force_refresh=true: re-runs pipeline synchronously and updates cache.
    - ?agent=true: uses the LangGraph B2B agent (bypasses cache).

    After serving a cached response the endpoint schedules a background
    refresh if the cache is older than half the TTL (3 hours), so the
    next request always gets fresh data without blocking.
    """
    logger.info(f"GET /bundles/{store_id} | force_refresh={force_refresh}, limit={limit}, agent={agent}")

    if agent:
        from app.agent.b2b.graph import run_b2b_agent
        bundles = await run_b2b_agent(store_id=store_id, top_k=limit)
        logger.info(f"Agent mode returned {len(bundles)} bundles for {store_id}")
        return bundles

    # if agent:
    #     from app.agent.b2b.graph import run_b2b_agent
    #     result = await run_b2b_agent(store_id=store_id, top_k=limit)
    #     return JSONResponse(content=result)

    firestore_client = get_firestore()

    # Synchronous refresh requested — run now and update cache
    if force_refresh or not _cache_valid(store_id):
        logger.info(f"Running pipeline for {store_id} (cache_valid={_cache_valid(store_id)}, force_refresh={force_refresh})")
        try:
            bundles = await run_pipeline(
                store_id=store_id,
                connector=connector,
                firestore_client=firestore_client,
                top_n=20,
                top_k_p2=20,
                top_k_p6=limit,
            )
            logger.info(f"Pipeline returned {len(bundles)} bundles for {store_id}")
        except Exception as e:
            logger.error(f"Pipeline error for {store_id}: {e}", exc_info=True)
            bundles = []

        _bundle_cache[store_id] = {
            "bundles": bundles,
            "generated_at": datetime.now(),
        }
        logger.info(f"Returning {len(bundles[:limit])} bundles (limit={limit})")
        return bundles[:limit]

    # Serve from cache; schedule a background refresh if older than half TTL
    entry = _bundle_cache.get(store_id)
    if not entry:
        # Cache entry doesn't exist yet (may have failed to populate)
        # Fall back to synchronous refresh
        logger.warning(f"Cache miss for {store_id}, running pipeline as fallback")
        try:
            bundles = await run_pipeline(
                store_id=store_id,
                connector=connector,
                firestore_client=firestore_client,
                top_n=20,
                top_k_p2=20,
                top_k_p6=limit,
            )
            logger.info(f"Fallback pipeline returned {len(bundles)} bundles for {store_id}")
        except Exception as e:
            logger.error(f"Fallback pipeline error for {store_id}: {e}", exc_info=True)
            bundles = []

        _bundle_cache[store_id] = {
            "bundles": bundles,
            "generated_at": datetime.now(),
        }
        return bundles[:limit]

    age = datetime.now() - entry["generated_at"]
    logger.info(f"Serving {len(entry['bundles'])} cached bundles for {store_id} (age={age.total_seconds():.0f}s)")
    if age > _CACHE_TTL / 2:
        logger.debug(f"Cache age ({age.total_seconds():.0f}s) > TTL/2, scheduling background refresh")
        background_tasks.add_task(_refresh_cache, store_id, connector, firestore_client)

    return entry["bundles"][:limit]


@router.post("/bundles/{store_id}/refresh")
async def trigger_bundle_refresh(
    store_id: str,
    background_tasks: BackgroundTasks,
    connector: StoreConnector = Depends(get_connector),
):
    """
    Trigger an async bundle pre-generation for a store.

    Designed for scheduled calls (cron / admin action) so the cache is
    always warm when the store opens. Returns immediately — the pipeline
    runs in the background.
    """
    firestore_client = get_firestore()
    background_tasks.add_task(_refresh_cache, store_id, connector, firestore_client)
    return {
        "store_id": store_id,
        "status": "refresh_scheduled",
        "message": "Bundle generation started in background. Use GET /bundles/{store_id} to retrieve when ready.",
    }


@router.get("/bundles/{store_id}/cache-status")
async def get_cache_status(store_id: str):
    """Return the current cache state for a store (age, valid, bundle count)."""
    entry = _bundle_cache.get(store_id)
    if not entry:
        return {"store_id": store_id, "cached": False}
    age_seconds = (datetime.now() - entry["generated_at"]).total_seconds()
    return {
        "store_id": store_id,
        "cached": True,
        "bundle_count": len(entry["bundles"]),
        "generated_at": entry["generated_at"].isoformat(),
        "age_seconds": round(age_seconds),
        "valid": _cache_valid(store_id),
    }
