"""
Admin Portal API endpoints (Feature 1).

GET /api/admin/combos       — List AI-suggested bundle combos for a store
GET /api/admin/inventory    — List inventory items nearing expiration
POST /api/admin/combos/{id}/accept  — Accept a combo suggestion
POST /api/admin/combos/{id}/reject  — Reject a combo suggestion
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from app.integrations.connectors.base import StoreConnector
from app.dependencies import get_connector, get_firestore
from app.core.pipeline.orchestrator import run_pipeline
from app.core.pipeline import p1_cache
from app.core.pipeline.p1_priority import run_p1
from app.core.data.repository import DataRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# In-memory store for accepted bundles (session-only, no persistence)
# Key: (store_id, combo_id) → ComboResponse
# ---------------------------------------------------------------------------
_accepted_bundles: dict[tuple[str, str], "ComboResponse"] = {}


def get_accepted_bundles(store_id: str) -> list["ComboResponse"]:
    """Return all accepted bundles for a given store."""
    return [v for (sid, _), v in _accepted_bundles.items() if sid == store_id]


# ---------------------------------------------------------------------------
# Request / Response models (matching frontend expectations)
# ---------------------------------------------------------------------------

class ComboIngredient(BaseModel):
    """Ingredient in a combo bundle."""
    name: str
    status: str  # e.g., "Normal" or "Khẩn Cấp" (Urgent)
    quantity: float
    unit: str


class ComboResponse(BaseModel):
    """Combo suggestion response."""
    id: str  # bundle_id
    name: str  # recipe_name
    discount: float  # discount_rate as percentage (0-100)
    confidence: float  # final_score as percentage (0-100)
    ingredients: List[ComboIngredient]
    originalPrice: float
    newPrice: float
    aiReasoning: Optional[str] = None


class InventoryItem(BaseModel):
    """Inventory item nearing expiration."""
    id: str  # sku_id
    name: str  # product_name
    weight: float  # remaining_qty_g
    daysLeft: int  # expiry_days
    limit: float  # threshold for warning
    status: str  # "Khẩn Cấp" | "Cảnh Báo" | "Bình Thường"


class ComboActionRequest(BaseModel):
    """Request to accept/reject a combo."""
    storeId: str
    reason: Optional[str] = None


class ComboAcceptData(BaseModel):
    """Combo data sent from the admin frontend on accept."""
    id: str
    name: str
    discount: float
    confidence: float
    ingredients: List[ComboIngredient]
    originalPrice: float
    newPrice: float
    aiReasoning: Optional[str] = None


class ComboAcceptRequest(BaseModel):
    """Request to accept a combo with full combo data."""
    storeId: str
    combo: ComboAcceptData


class ComboActionResponse(BaseModel):
    """Response from accepting/rejecting a combo."""
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _bundle_to_combo(bundle) -> ComboResponse:
    """Convert a BundleOutput object or dict to ComboResponse."""
    # Normalise: agent returns dicts, pipeline returns BundleOutput objects
    if isinstance(bundle, dict):
        from app.core.models.bundle import BundleOutput
        bundle = BundleOutput.model_validate(bundle)

    _STATUS_MAP = {"CRITICAL": "Khẩn Cấp", "HIGH": "Cảnh Báo"}

    ingredients = [
        ComboIngredient(
            name=ing.product_name or ing.ingredient_id,
            status=_STATUS_MAP.get(ing.urgency_flag, "Bình Thường"),
            quantity=ing.qty_taken_g,
            unit="g",
        )
        for ing in bundle.ingredients
    ]
    return ComboResponse(
        id=bundle.bundle_id,
        name=bundle.recipe_name,
        discount=round(bundle.discount_rate * 100, 2),
        confidence=round(bundle.final_score * 100, 2),
        ingredients=ingredients,
        originalPrice=bundle.original_price,
        newPrice=bundle.final_price,
        aiReasoning=f"Waste reduction score: {bundle.waste_score_normalized:.2f}, "
                    f"Completeness: {bundle.completeness_score:.2f}",
    )


@router.get("/combos", response_model=List[ComboResponse])
async def get_admin_combos(
    storeId: str = Query(..., description="Store ID e.g., BHX-HCM001"),
    limit: int = Query(10, ge=1, le=20, description="Max combos to return"),
    connector: StoreConnector = Depends(get_connector),
):
    """
    Get AI-suggested bundle combos for a store.

    Agent (LangGraph B2B) is tried first for richer reasoning.
    Falls back to the deterministic P1-P7 pipeline if the agent fails or returns empty.
    """
    # --- Agent path (primary) ---
    try:
        from app.agent.b2b.graph import run_b2b_agent
        agent_bundles = await run_b2b_agent(store_id=storeId, top_k=limit)
        if agent_bundles:
            logger.info(f"Agent returned {len(agent_bundles)} bundles for {storeId}")
            return [_bundle_to_combo(b) for b in agent_bundles]
        logger.warning(f"Agent returned empty for {storeId}, falling back to pipeline")
    except Exception as e:
        logger.warning(f"Agent failed for {storeId} ({e}), falling back to pipeline")

    # --- Pipeline fallback ---
    try:
        firestore_client = get_firestore()
        bundles = await run_pipeline(
            store_id=storeId,
            connector=connector,
            firestore_client=firestore_client,
            top_k_p6=limit,
        )
        return [_bundle_to_combo(b) for b in bundles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch combos: {str(e)}")


async def _run_p1_warmup(store_id: str, connector: StoreConnector) -> None:
    """Background task: run P1 and populate p1_cache so /inventory and the agent are fast."""
    try:
        repo = DataRepository.get()
        batches_raw = connector.get_batches(store_id)
        batches = []
        for b in batches_raw:
            if hasattr(b, "model_dump"):
                d = b.model_dump()
            elif hasattr(b, "dict"):
                d = b.dict()
            elif isinstance(b, dict):
                d = b
            else:
                d = dict(b)
            if "remaining_qty_g" not in d:
                d["remaining_qty_g"] = d.get("unit_count", 1) * d.get("pack_size_g", 500)
            batches.append(d)

        all_sku_ids = {b["sku_id"] for b in batches}
        sales_history = {sku_id: connector.get_sales_history(store_id, sku_id) for sku_id in all_sku_ids}

        p1_scores = run_p1(batches, sales_history, repo.sku_lookup(), top_n=len(batches))
        p1_cache.put(store_id, p1_scores)
        logger.info(f"P1 warmup complete for {store_id}: {len(p1_scores)} scores cached")
    except Exception as e:
        logger.error(f"P1 warmup failed for {store_id}: {e}", exc_info=True)


@router.post("/cache/invalidate")
async def invalidate_cache(
    storeId: str = Query(..., description="Store ID to invalidate P1 cache for"),
):
    """
    Invalidate the P1 urgency score cache for a store.

    Call this after regenerating mock data or importing new batch data so that
    the next /combos or /inventory request re-computes scores from fresh batches.
    """
    p1_cache.invalidate(storeId)
    return {"status": "invalidated", "store_id": storeId}


@router.post("/warmup")
async def warmup_inventory(
    background_tasks: BackgroundTasks,
    storeId: str = Query(..., description="Store ID to pre-compute P1 urgency scores for"),
    connector: StoreConnector = Depends(get_connector),
):
    """
    Pre-compute P1 urgency scores for a store in the background.

    Call this when the admin frontend loads so that /inventory and the B2B agent
    can serve from cache instead of re-running P1 on their first request.
    Returns immediately; scoring runs asynchronously.
    """
    background_tasks.add_task(_run_p1_warmup, storeId, connector)
    return {"status": "warming_up", "store_id": storeId}


_URGENCY_TO_STATUS = {
    "CRITICAL": "Khẩn Cấp",
    "HIGH":     "Cảnh Báo",
    "MEDIUM":   "Bình Thường",
    "WATCH":    "Bình Thường",
}
_URGENCY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "WATCH": 3}


@router.get("/inventory", response_model=List[InventoryItem])
async def get_admin_inventory(
    storeId: str = Query(..., description="Store ID e.g., BHX-HCM001"),
    daysThreshold: int = Query(14, ge=1, le=30, description="Days until expiry to flag"),
    connector: StoreConnector = Depends(get_connector),
):
    """
    Get inventory items nearing expiration.

    Uses P1 priority scores (composite of expiry decay, supply/demand, sell-through)
    to determine urgency. Reads from a shared cache populated when /combos runs;
    falls back to running P1 directly if the cache is cold.
    """
    try:
        repo = DataRepository.get()
        sku_dict = repo.sku_dict_lookup()

        # Try warm cache first (populated by /combos pipeline run)
        p1_scores = p1_cache.get(storeId)

        if p1_scores is None:
            # Cold path: run P1 directly without the full P1→P7 pipeline
            batches_raw = connector.get_batches(storeId)
            batches = []
            for b in batches_raw:
                if hasattr(b, "model_dump"):
                    batch_dict = b.model_dump()
                elif hasattr(b, "dict"):
                    batch_dict = b.dict()
                elif isinstance(b, dict):
                    batch_dict = b
                else:
                    batch_dict = vars(b)
                if "remaining_qty_g" not in batch_dict and "unit_count" in batch_dict and "pack_size_g" in batch_dict:
                    batch_dict["remaining_qty_g"] = batch_dict["unit_count"] * batch_dict["pack_size_g"]
                batches.append(batch_dict)

            all_sku_ids = {b["sku_id"] for b in batches}
            sales_history = {sku_id: connector.get_sales_history(storeId, sku_id) for sku_id in all_sku_ids}

            p1_scores = run_p1(batches, sales_history, repo.sku_lookup(), top_n=len(batches))
            p1_cache.put(storeId, p1_scores)

        # Aggregate P1Output by SKU: sum weight, min expiry_days, highest urgency
        sku_agg: dict[str, dict] = {}
        for item in p1_scores:
            sku_id = item.sku_id
            if sku_id not in sku_agg:
                sku_agg[sku_id] = {
                    "name": sku_dict.get(sku_id, {}).get("product_name", sku_id),
                    "weight": 0.0,
                    "min_days_left": item.expiry_days,
                    "urgency_rank": _URGENCY_RANK[item.urgency_flag],
                    "urgency_flag": item.urgency_flag,
                }
            agg = sku_agg[sku_id]
            agg["weight"] += item.remaining_qty_g
            agg["min_days_left"] = min(agg["min_days_left"], item.expiry_days)
            rank = _URGENCY_RANK[item.urgency_flag]
            if rank < agg["urgency_rank"]:
                agg["urgency_rank"] = rank
                agg["urgency_flag"] = item.urgency_flag

        # Sort by urgency rank then expiry days, then build response
        sorted_skus = sorted(
            sku_agg.items(),
            key=lambda kv: (kv[1]["urgency_rank"], kv[1]["min_days_left"]),
        )

        return [
            InventoryItem(
                id=sku_id,
                name=agg["name"],
                weight=agg["weight"],
                daysLeft=max(0, agg["min_days_left"]),
                limit=daysThreshold,
                status=_URGENCY_TO_STATUS[agg["urgency_flag"]],
            )
            for sku_id, agg in sorted_skus
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch inventory: {str(e)}")


@router.post("/combos/{combo_id}/accept", response_model=ComboActionResponse)
async def accept_combo(
    combo_id: str,
    req: ComboAcceptRequest,
):
    """
    Accept a combo suggestion.

    Stores the full combo data in-memory so the customer endpoint can serve it.
    """
    try:
        combo = ComboResponse(
            id=req.combo.id,
            name=req.combo.name,
            discount=req.combo.discount,
            confidence=req.combo.confidence,
            ingredients=req.combo.ingredients,
            originalPrice=req.combo.originalPrice,
            newPrice=req.combo.newPrice,
            aiReasoning=req.combo.aiReasoning,
        )
        _accepted_bundles[(req.storeId, combo_id)] = combo
        logger.info(f"Combo {combo_id} accepted for store {req.storeId}, total accepted: {len(get_accepted_bundles(req.storeId))}")
        return ComboActionResponse(
            success=True,
            message=f"Combo {combo_id} accepted for store {req.storeId}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to accept combo: {str(e)}")


@router.post("/combos/{combo_id}/reject", response_model=ComboActionResponse)
async def reject_combo(
    combo_id: str,
    req: ComboActionRequest,
):
    """
    Reject a combo suggestion.

    Records that the admin rejected this combo.
    Tracked as an event for analytics and agent feedback.
    """
    try:
        # TODO: Implement combo rejection tracking
        # For now, just log the action
        return ComboActionResponse(
            success=True,
            message=f"Combo {combo_id} rejected for store {req.storeId}. Reason: {req.reason or 'Not specified'}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject combo: {str(e)}")
