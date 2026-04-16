"""
LangChain @tool wrappers for the B2B Store Bundle Agent.

Uses tool_factory to reduce boilerplate. The finalize_bundles tool is special:
it accepts only recipe_ids (not full recipe dicts) and runs FEFO allocation
internally so the LLM cannot corrupt ingredient_status / batches_used data.
"""

import json
import logging
from typing import List

from langchain_core.tools import tool

from app.agent.tools import (
    search_recipes_from_ingredients as _search_recipes,
    check_feasibility_and_substitute as _check_feasibility,
)
from app.agent.shared.tool_factory import make_tool
from app.agent.shared.ontology import query_ontology as _query_ontology
from app.core.data.repository import DataRepository

logger = logging.getLogger(__name__)

# Auto-wrap core tools using factory
search_recipes_from_ingredients = make_tool(
    _search_recipes,
    description="Tìm công thức sử dụng nhiều nguyên liệu urgent nhất."
)

check_feasibility_and_substitute = make_tool(
    _check_feasibility,
    description="Kiểm tra khả thi của một recipe và gợi ý thay thế."
)

query_ontology = make_tool(
    _query_ontology,
    description="Tra cứu ontology để tìm nguyên liệu thay thế."
)


@tool
def finalize_bundles(recipe_ids: List[str], store_id: str, top_k: int = 10) -> str:
    """
    TOOL CUỐI CÙNG - Gọi khi đã có danh sách recipe_id khả thi.

    Nhận recipe_ids (ví dụ ["R004", "R017"]) và store_id.
    Tự động chạy FEFO allocation, P5, P6, P7 để tạo bundles hoàn chỉnh với giá.

    KHÔNG cần truyền full recipe dicts hay ingredient_status — chỉ cần recipe_id.
    """
    try:
        from app.core.pipeline.p5_waste import run_p5
        from app.core.pipeline.p6_ranking import run_p6
        from app.core.pipeline.p7_pricing import run_p7
        from app.agent.tools import get_urgent_inventory

        repo = DataRepository.get()
        sku_lookup = repo.sku_dict_lookup()
        recipe_names = repo.recipe_names()
        recipe_lookup = repo.recipe_lookup()

        logger.info(f"finalize_bundles called: recipe_ids={recipe_ids}, store_id={store_id}, top_k={top_k}")

        # ── Step 1: Build urgency lookup from store's urgent inventory ──────────
        urgent_batches = get_urgent_inventory(store_id, top_n=50)
        p1_ingredient_lookup: dict[str, str] = {}
        p1_score_lookup: dict[str, float] = {}
        for b in urgent_batches:
            ing_id = b.get("ingredient_id")
            score = b.get("priority_score", 0.0)
            if ing_id:
                p1_score_lookup[ing_id] = max(p1_score_lookup.get(ing_id, 0.0), score)
                if score >= 0.80:
                    p1_ingredient_lookup[ing_id] = "CRITICAL"
                elif score >= 0.65:
                    p1_ingredient_lookup[ing_id] = "HIGH"
                elif score >= 0.50:
                    p1_ingredient_lookup[ing_id] = "MEDIUM"
                else:
                    p1_ingredient_lookup[ing_id] = "WATCH"

        # ── Step 2: Run FEFO allocation for each recipe internally ──────────────
        validated_recipes = []
        for recipe_id in recipe_ids:
            recipe = recipe_lookup.get(recipe_id)
            if not recipe:
                logger.warning(f"Recipe {recipe_id} not found, skipping")
                continue

            recipe_with_store = {**recipe, "store_id": store_id}
            result = _check_feasibility(recipe_with_store)

            logger.debug(
                f"  {recipe_id}: feasible={result.get('feasible')}, "
                f"completeness={result.get('completeness_score')}, "
                f"ingredient_status_count={len(result.get('ingredient_status', []))}"
            )

            enriched = result["recipe"].copy()
            enriched["ingredient_status"] = result["ingredient_status"]
            enriched["completeness_score"] = result["completeness_score"]
            enriched["store_id"] = store_id

            # Fields required by P5/P6: matched_ingredients must have priority_score per item
            recipe_ings = enriched.get("ingredients", [])
            enriched["matched_ingredients"] = [
                {
                    "ingredient_id": ing["ingredient_id"],
                    "priority_score": p1_score_lookup.get(ing["ingredient_id"], 0.0),
                }
                for ing in recipe_ings
                if ing["ingredient_id"] in p1_score_lookup
            ] or [
                {"ingredient_id": ing["ingredient_id"], "priority_score": 0.0}
                for ing in recipe_ings
            ]
            enriched.setdefault("urgency_coverage_score", result.get("completeness_score", 0.65))
            enriched.setdefault("waste_score_normalized", 0.5)
            enriched.setdefault("priority_score", round(result.get("completeness_score", 0.6) * 0.8, 4))

            statuses = enriched["ingredient_status"]
            fulfilled = [s for s in statuses if s.get("status") in ("fulfilled", "substitute")]
            deviations = [s.get("deviation", 0.0) for s in fulfilled]
            enriched["avg_deviation"] = sum(deviations) / len(deviations) if deviations else 0.0
            enriched["total_rounding_loss_g"] = 0.0

            validated_recipes.append(enriched)

        logger.info(f"finalize_bundles: {len(validated_recipes)}/{len(recipe_ids)} recipes passed allocation")

        if not validated_recipes:
            return json.dumps({"error": "No recipes passed allocation"}, ensure_ascii=False)

        # ── Step 3: Run P5 → P6 → P7 ───────────────────────────────────────────
        p5_output = run_p5(validated_recipes, sku_lookup)
        p6_output = run_p6(p5_output, store_id, None, None, top_k=top_k)

        try:
            final_bundles = run_p7(p6_output, sku_lookup, recipe_names, store_id,
                                   p1_ingredient_lookup=p1_ingredient_lookup)
        except Exception as p7_err:
            logger.warning(f"P7 failed ({p7_err}), falling back to P6 output")
            final_bundles = p6_output

        result_list = []
        for bundle in final_bundles:
            if hasattr(bundle, "model_dump"):
                result_list.append(bundle.model_dump())
            elif isinstance(bundle, dict):
                result_list.append(bundle)

        logger.info(f"finalize_bundles: returning {len(result_list)} bundles")
        return json.dumps(result_list, ensure_ascii=False, default=str)

    except Exception as e:
        import traceback
        logger.error(f"finalize_bundles error: {e}", exc_info=True)
        return json.dumps({
            "error": f"Finalize failed: {str(e)}",
            "detail": traceback.format_exc()[-800:]
        }, ensure_ascii=False)


# All B2B tools for LangGraph agent registration
b2b_langchain_tools = [
    search_recipes_from_ingredients,
    check_feasibility_and_substitute,
    query_ontology,
    finalize_bundles,
]
