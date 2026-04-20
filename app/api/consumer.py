"""
Consumer API endpoints.

GET /api/customer/combos     — List combo bundles for shopping (Feature 1 consumer view)
POST /consumer/chat          — Multi-turn conversation with the cooking assistant (Feature 2)
POST /consumer/suggest       — One-shot recipe suggestion from ingredient list (Feature 2)
"""

from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.agent.consumer.graph import chat, suggest

router = APIRouter(prefix="/consumer", tags=["consumer"])
customer_router = APIRouter(tags=["consumer"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message in Vietnamese")
    thread_id: str = Field(..., description="Conversation thread ID for multi-turn state")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    allergies: Optional[list[str]] = Field(None, description="Ingredient names the user is allergic to")
    dietary_preferences: Optional[list[str]] = Field(None, description="e.g. ['vegetarian']")


class ShoppingItem(BaseModel):
    ingredient_id: str
    name: str
    required_qty_g: float
    unit: str = "g"
    is_optional: bool = False
    estimated_unit_price: float = 0.0
    sku_id: Optional[str] = None


class RecipeSuggestionIngredient(BaseModel):
    name: str
    have: bool = False
    optional: bool = False


class RecipeSuggestion(BaseModel):
    recipe_id: str
    name: str
    score: float = 0.0
    ingredients: List[RecipeSuggestionIngredient] = []


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Agent response in Vietnamese")
    thread_id: str
    shopping_list: Optional[List[ShoppingItem]] = Field(None)
    recipe_suggestions: Optional[List[RecipeSuggestion]] = Field(None)


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

    reply, raw_sl, raw_suggestions = await chat(
        message=req.message,
        thread_id=req.thread_id,
        user_context=user_context,
    )

    sl = None
    if raw_sl:
        try:
            sl = [ShoppingItem(**item) for item in raw_sl if isinstance(item, dict) and "ingredient_id" in item]
        except Exception:
            sl = None

    suggestions = None
    if raw_suggestions:
        try:
            suggestions = [RecipeSuggestion(**s) for s in raw_suggestions if isinstance(s, dict)]
        except Exception:
            suggestions = None

    return ChatResponse(reply=reply, thread_id=req.thread_id, shopping_list=sl or None, recipe_suggestions=suggestions or None)


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
    quantity: float = 0.0
    unit: str = "g"
    retailPrice: float = 0.0


class CustomerComboTime(BaseModel):
    """Recipe timing metadata for customer view."""
    prepMinutes: int
    cookMinutes: int
    totalMinutes: int


class CustomerComboResponse(BaseModel):
    """Combo for customer shopping portal."""
    id: str
    name: str
    description: Optional[str] = None
    discount: float  # Discount percentage (0-100)
    confidence: float = 0.0
    originalPrice: float
    newPrice: float
    tags: List[str] = []
    image: Optional[str] = None
    ingredients: List[CustomerComboIngredient]
    instructions: List[str] = []
    time: Optional[CustomerComboTime] = None
    aiReasoning: Optional[str] = None


@customer_router.get("/api/customer/combos", response_model=List[CustomerComboResponse])
async def get_customer_combos(
    storeId: str = Query(..., description="Store ID e.g., BHX-HCM001"),
    limit: int = Query(10, ge=1, le=20, description="Max combos to return"),
):
    """
    Get combo bundles for customer shopping portal.

    Returns only admin-accepted combos. If no combos have been accepted
    for this store, returns an empty list.
    """
    from app.api.admin import get_accepted_bundles

    accepted = get_accepted_bundles(storeId)

    combos = []
    for combo in accepted[:limit]:
        ingredients = [
            CustomerComboIngredient(
                name=ing.name,
                status="Sắp hết" if ing.status == "Khẩn Cấp" else "Bình thường",
                quantity=ing.quantity,
                unit=ing.unit,
                retailPrice=ing.retailPrice,
            )
            for ing in combo.ingredients
        ]

        combos.append(CustomerComboResponse(
            id=combo.id,
            name=combo.name,
            description=combo.description or f"Công thức làm {combo.name} từ hàng sẵn có",
            discount=combo.discount,
            confidence=combo.confidence,
            originalPrice=combo.originalPrice,
            newPrice=combo.newPrice,
            tags=combo.tags or ["Khuyến mại", "Bền vững"],
            ingredients=ingredients,
            instructions=combo.instructions or [
                "Chuẩn bị các nguyên liệu",
                "Nấu theo công thức",
                "Dùng nóng",
            ],
            time=CustomerComboTime.model_validate(combo.time.model_dump()) if combo.time else None,
            aiReasoning=combo.aiReasoning,
        ))

    return combos
