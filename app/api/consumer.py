"""
Consumer API endpoints.

GET /api/customer/combos     — List combo bundles for shopping (Feature 1 consumer view)
POST /consumer/chat          — Multi-turn conversation with the cooking assistant (Feature 2)
POST /consumer/suggest       — One-shot recipe suggestion from ingredient list (Feature 2)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.integrations.connectors.base import StoreConnector
from app.dependencies import get_connector
from app.agent.consumer.graph import chat, suggest

router = APIRouter(prefix="/consumer", tags=["consumer"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message in Vietnamese")
    thread_id: str = Field(..., description="Conversation thread ID for multi-turn state")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    allergies: Optional[list[str]] = Field(None, description="Ingredient names the user is allergic to")
    dietary_preferences: Optional[list[str]] = Field(None, description="e.g. ['vegetarian']")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Agent response in Vietnamese")
    thread_id: str


class SuggestRequest(BaseModel):
    ingredients: list[str] = Field(..., description="Ingredient names in Vietnamese, e.g. ['thịt heo', 'cà chua']")
    allergies: Optional[list[str]] = Field(None, description="Ingredient names the user is allergic to")
    top_k: int = Field(3, ge=1, le=10, description="Number of suggestions to return")


class SuggestResponse(BaseModel):
    resolved_ingredients: list[dict]
    unresolved_ingredients: list[str]
    allergy_ids: list[str]
    suggestions: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def consumer_chat(req: ChatRequest):
    """
    Multi-turn conversation with the Consumer Cooking Assistant.

    Send a message and receive a contextual reply. The agent remembers
    previous messages in the same thread_id.

    Pass allergies/dietary_preferences on the first message of a conversation
    to set the user's context.
    """
    user_context = None
    if req.allergies or req.dietary_preferences:
        user_context = {
            "user_id": req.user_id,
            "allergies": req.allergies or [],
            "dietary_preferences": req.dietary_preferences or [],
        }

    reply = await chat(
        message=req.message,
        thread_id=req.thread_id,
        user_context=user_context,
    )

    return ChatResponse(reply=reply, thread_id=req.thread_id)


@router.post("/suggest", response_model=SuggestResponse)
async def consumer_suggest(req: SuggestRequest):
    """
    One-shot recipe suggestion from a list of ingredients.

    No conversation state — returns immediate recipe recommendations
    based on the provided ingredients, with allergy filtering.
    """
    result = await suggest(
        ingredients=req.ingredients,
        allergies=req.allergies,
        top_k=req.top_k,
    )

    return SuggestResponse(**result)


# ---------------------------------------------------------------------------
# Customer Shopping Portal
# ---------------------------------------------------------------------------

class CustomerComboIngredient(BaseModel):
    """Ingredient in a combo for customer view."""
    name: str
    status: str  # e.g., "Normal", "Sắp hết"


class CustomerComboResponse(BaseModel):
    """Combo for customer shopping portal."""
    id: str
    name: str
    description: Optional[str] = None
    discount: float  # Discount percentage (0-100)
    originalPrice: float
    newPrice: float
    tags: List[str] = []
    image: Optional[str] = None
    ingredients: List[CustomerComboIngredient]
    instructions: List[str] = []


@router.get("/api/customer/combos", response_model=List[CustomerComboResponse])
async def get_customer_combos(
    storeId: str = Query(..., description="Store ID e.g., BHX-HCM001"),
    limit: int = Query(10, ge=1, le=20, description="Max combos to return"),
    connector: StoreConnector = Depends(get_connector),
):
    """
    Get combo bundles for customer shopping portal.

    Returns available combos with pricing and ingredient details.
    Optimized for customer-facing view with discounts highlighted.
    """
    from app.core.pipeline.orchestrator import run_pipeline

    firestore_client = None
    try:
        firestore_client = get_connector.__self__.firestore_client
    except:
        pass

    try:
        # Call the backend pipeline to get bundles
        bundles = await run_pipeline(
            store_id=storeId,
            connector=connector,
            firestore_client=firestore_client,
            top_k_p6=limit,
        )

        # Convert BundleOutput to CustomerComboResponse format
        combos = []
        for bundle in bundles:
            ingredients = [
                CustomerComboIngredient(
                    name=ing.product_name or ing.ingredient_id,
                    status="Bình thường" if not ing.urgency_flag else "Sắp hết",
                )
                for ing in bundle.ingredients
            ]

            # Add recipe instructions if available
            instructions = []
            # TODO: Get instructions from recipe data if available
            instructions = [
                "Chuẩn bị các nguyên liệu",
                "Nấu theo công thức",
                "Dùng nóng",
            ]

            combo = CustomerComboResponse(
                id=bundle.bundle_id,
                name=bundle.recipe_name,
                description=f"Công thức làm {bundle.recipe_name} từ hàng sẵn có",
                discount=bundle.discount_rate * 100,  # Convert to percentage
                originalPrice=bundle.original_price,
                newPrice=bundle.final_price,
                tags=["Khuyến mại", "Bền vững"],
                ingredients=ingredients,
                instructions=instructions,
            )
            combos.append(combo)

        return combos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch customer combos: {str(e)}")
