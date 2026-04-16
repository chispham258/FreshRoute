from typing import List, Optional

from pydantic import BaseModel


class RecipeRequirement(BaseModel):
    ingredient_id: str
    required_qty_g: float
    is_optional: bool = False
    role: Optional[str] = None


class Recipe(BaseModel):
    recipe_id: str
    name: str
    servings: int = 2
    category: Optional[str] = None
    ingredients: List[RecipeRequirement] = []
