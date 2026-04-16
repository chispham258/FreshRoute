"""
Admin Portal API endpoints (Feature 1).

GET /api/admin/combos       — List AI-suggested bundle combos for a store
GET /api/admin/inventory    — List inventory items nearing expiration
POST /api/admin/combos/{id}/accept  — Accept a combo suggestion
POST /api/admin/combos/{id}/reject  — Reject a combo suggestion
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.integrations.connectors.base import StoreConnector
from app.dependencies import get_connector, get_firestore
from app.core.pipeline.orchestrator import run_pipeline

router = APIRouter(prefix="/api/admin", tags=["admin"])


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


class ComboActionResponse(BaseModel):
    """Response from accepting/rejecting a combo."""
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/combos", response_model=List[ComboResponse])
async def get_admin_combos(
    storeId: str = Query(..., description="Store ID e.g., BHX-HCM001"),
    limit: int = Query(10, ge=1, le=20, description="Max combos to return"),
    connector: StoreConnector = Depends(get_connector),
):
    """
    Get AI-suggested bundle combos for a store.

    Returns top-K combo recommendations with ingredients, pricing, and confidence scores.
    Suitable for admin review before promoting to customers.
    """
    firestore_client = get_firestore()

    try:
        # Call the backend pipeline to get bundles
        bundles = await run_pipeline(
            store_id=storeId,
            connector=connector,
            firestore_client=firestore_client,
            top_k_p6=limit,
        )

        # Convert BundleOutput to ComboResponse format
        combos = []
        for bundle in bundles:
            ingredients = [
                ComboIngredient(
                    name=ing.product_name or ing.ingredient_id,
                    status="Khẩn Cấp" if ing.urgency_flag else "Normal",
                    quantity=ing.qty_taken_g,
                    unit="g",
                )
                for ing in bundle.ingredients
            ]

            combo = ComboResponse(
                id=bundle.bundle_id,
                name=bundle.recipe_name,
                discount=bundle.discount_rate * 100,  # Convert to percentage
                confidence=bundle.final_score * 100,  # Convert to percentage
                ingredients=ingredients,
                originalPrice=bundle.original_price,
                newPrice=bundle.final_price,
                aiReasoning=f"Waste reduction score: {bundle.waste_score_normalized:.2f}, "
                             f"Completeness: {bundle.completeness_score:.2f}",
            )
            combos.append(combo)

        return combos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch combos: {str(e)}")


@router.get("/inventory", response_model=List[InventoryItem])
async def get_admin_inventory(
    storeId: str = Query(..., description="Store ID e.g., BHX-HCM001"),
    daysThreshold: int = Query(14, ge=1, le=30, description="Days until expiry to flag"),
    connector: StoreConnector = Depends(get_connector),
):
    """
    Get inventory items nearing expiration.

    Lists all SKUs with their expiry status. Items expiring within `daysThreshold` days
    are marked as "Khẩn Cấp" (Urgent) or "Cảnh Báo" (Warning).
    """
    try:
        # Get store data
        store_data = await connector.get_store_by_id(storeId)
        if not store_data:
            raise HTTPException(status_code=404, detail=f"Store {storeId} not found")

        batches = store_data.get("batches", [])
        sku_lookup = store_data.get("sku_lookup", {})

        # Group by SKU to get aggregate inventory
        sku_inventory = {}

        for batch in batches:
            sku_id = batch["sku_id"]
            expiry_date = datetime.fromisoformat(batch["expiry_date"])
            days_left = (expiry_date - datetime.now()).days

            if sku_id not in sku_inventory:
                sku = sku_lookup.get(sku_id, {})
                sku_inventory[sku_id] = {
                    "name": sku.get("product_name", sku_id),
                    "weight": 0,
                    "min_days_left": days_left,
                }

            sku_inventory[sku_id]["weight"] += batch.get("remaining_qty_g", 0)
            sku_inventory[sku_id]["min_days_left"] = min(
                sku_inventory[sku_id]["min_days_left"], days_left
            )

        # Build response
        inventory = []
        for sku_id, data in sku_inventory.items():
            days_left = max(0, data["min_days_left"])

            # Determine status
            if days_left <= 3:
                status = "Khẩn Cấp"  # Urgent
            elif days_left <= 7:
                status = "Cảnh Báo"  # Warning
            else:
                status = "Bình Thường"  # Normal

            item = InventoryItem(
                id=sku_id,
                name=data["name"],
                weight=data["weight"],
                daysLeft=days_left,
                limit=daysThreshold,
                status=status,
            )
            inventory.append(item)

        # Sort by urgency (Urgent first, then Warning, then Normal)
        status_order = {"Khẩn Cấp": 0, "Cảnh Báo": 1, "Bình Thường": 2}
        inventory.sort(key=lambda x: (status_order.get(x.status, 3), x.daysLeft))

        return inventory

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch inventory: {str(e)}")


@router.post("/combos/{combo_id}/accept", response_model=ComboActionResponse)
async def accept_combo(
    combo_id: str,
    req: ComboActionRequest,
):
    """
    Accept a combo suggestion.

    Records that the admin accepted this combo for promotion to customers.
    Tracked as an event for analytics.
    """
    try:
        # TODO: Implement combo acceptance tracking
        # For now, just log the action
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
