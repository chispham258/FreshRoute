"""
Seed PostgreSQL with mock data from fixture files.

Run: python -m scripts.seed_db
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        # Load fixtures
        with open(FIXTURES_DIR / "mock_skus.json") as f:
            skus = json.load(f)
        with open(FIXTURES_DIR / "mock_recipes.json") as f:
            recipes = json.load(f)

        # Seed product_sku
        for sku in skus:
            await conn.execute(
                text("""
                    INSERT INTO product_sku (sku_id, ingredient_id, product_name, category_l1, category_l2,
                        unit_type, pack_size_g, retail_price, cost_price, typical_shelf_life_days)
                    VALUES (:sku_id, :ingredient_id, :product_name, :category_l1, :category_l2,
                        :unit_type, :pack_size_g, :retail_price, :cost_price, :typical_shelf_life_days)
                    ON CONFLICT (sku_id) DO NOTHING
                """),
                sku,
            )

        # Seed recipe + recipe_requirement
        for recipe in recipes:
            await conn.execute(
                text("""
                    INSERT INTO recipe (recipe_id, name, servings, category)
                    VALUES (:recipe_id, :name, :servings, :category)
                    ON CONFLICT (recipe_id) DO NOTHING
                """),
                {
                    "recipe_id": recipe["recipe_id"],
                    "name": recipe["name"],
                    "servings": recipe["servings"],
                    "category": recipe["category"],
                },
            )
            for ing in recipe["ingredients"]:
                await conn.execute(
                    text("""
                        INSERT INTO recipe_requirement (recipe_id, ingredient_id, required_qty_g, is_optional, role)
                        VALUES (:recipe_id, :ingredient_id, :required_qty_g, :is_optional, :role)
                        ON CONFLICT (recipe_id, ingredient_id) DO NOTHING
                    """),
                    {
                        "recipe_id": recipe["recipe_id"],
                        **ing,
                    },
                )

    await engine.dispose()
    print(f"Seeded {len(skus)} SKUs and {len(recipes)} recipes.")


if __name__ == "__main__":
    asyncio.run(seed())
