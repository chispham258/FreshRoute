"""
Consumer Agent state for Feature 2 — Home Cooking Assistant.

Extends the base AgentState with consumer-specific fields:
user identity, allergies, conversation mode, and urgent ingredient tracking.
"""

from typing import List, Literal, Optional

from typing_extensions import TypedDict

from app.agent.state import AgentState


class UserIngredient(TypedDict):
    """A single ingredient in the user's home inventory."""
    ingredient_id: str
    quantity_g: float
    expiry_date: str          # ISO format date string
    expiry_days: int          # days until expiry (pre-computed)


class ConsumerState(AgentState):
    """
    State for the Consumer Home Cooking Agent.

    Supports two flows:
      Flow 1 (Recipe-Driven): User wants a specific dish.
      Flow 2 (Inventory-Driven): User doesn't know what to cook.
    """
    # --- user identity ---
    user_id: str

    # --- user preferences ---
    allergies: List[str]                                    # e.g. ["tom", "sua_tuoi"]
    dietary_preferences: List[str]                          # e.g. ["vegetarian", "low_sodium"]

    # --- user home inventory ---
    user_inventory: List[UserIngredient]
    urgent_ingredients: List[UserIngredient]                 # expiry_days <= 3

    # --- conversation ---
    conversation_mode: Literal["recipe_driven", "inventory_driven"]
    target_recipe: Optional[str]                            # recipe name/id for Flow 1

    # --- agent output ---
    suggested_recipes: List[dict]                           # recipes matched to inventory
    adjusted_recipe: Optional[dict]                         # final recipe with substitutions
