"""
Orchestrator — Runs the complete pipeline P1 -> P2 -> P3 -> P5 -> P6 -> P7.

Uses Chain of Responsibility pattern (PipelineStage) and DataRepository for
centralized data access and state management.
"""

from typing import List

from app.integrations.connectors.base import StoreConnector
from app.core.data.repository import DataRepository
from app.core.models.bundle import BundleOutput
from app.core.pipeline.base import PipelineContext, PipelineStage, PipelineChain
from app.core.pipeline.p1_priority import run_p1
from app.core.pipeline import p1_cache
from app.core.pipeline.p2_retrieval import run_p2
from app.core.pipeline.p3_feasibility import run_p3
from app.core.pipeline.p5_waste import run_p5
from app.core.pipeline.p6_ranking import run_p6
from app.core.pipeline.p7_pricing import run_p7


# ============================================================================
# Pipeline Stage Implementations
# ============================================================================


class P1_PriorityStage(PipelineStage):
    """P1: Priority Scoring — batch scoring by expiry urgency."""

    def run(self, context: PipelineContext) -> PipelineContext:
        context.p1_output = run_p1(
            context.batches,
            context.sales_history,
            context.sku_lookup,
            top_n=context.top_n,
        )
        # Build lookup for urgency_flag enrichment in P7
        # NOTE: p1_output items are P1Output Pydantic models, use attribute access not dict
        context.p1_ingredient_lookup = {
            item.ingredient_id: item.urgency_flag
            for item in context.p1_output
        }
        return context


class P2_RetrievalStage(PipelineStage):
    """P2: Recipe Retrieval — candidate recipes matching scored batches."""

    def run(self, context: PipelineContext) -> PipelineContext:
        context.p2_output = run_p2(
            context.p1_output,
            context.inverted_index,
            context.recipe_lookup,
            top_k=context.top_k_p2,
        )
        return context


class P3_FeasibilityStage(PipelineStage):
    """P3: Feasibility Validation — check recipe satisfaction & substitutions."""

    def run(self, context: PipelineContext) -> PipelineContext:
        context.p3_output = run_p3(
            context.p2_output,
            context.recipe_requirements,
            context.batches,
            context.substitute_groups,
        )
        return context


class P5_WasteStage(PipelineStage):
    """P5: Waste Scoring — compute waste metrics per recipe."""

    def run(self, context: PipelineContext) -> PipelineContext:
        context.p5_output = run_p5(context.p3_output, context.sku_dict_lookup)
        return context


class P6_RankingStage(PipelineStage):
    """P6: Multi-objective Ranking — balance waste, urgency, margin."""

    def run(self, context: PipelineContext) -> PipelineContext:
        context.p6_output = run_p6(
            context.p5_output,
            context.store_id,
            None,  # firestore_client not yet available in PipelineContext
            top_k=context.top_k_p6,
        )
        return context


class P7_PricingStage(PipelineStage):
    """P7: Dynamic Pricing — final bundle composition with pricing."""

    def run(self, context: PipelineContext) -> PipelineContext:
        context.final_bundles = run_p7(
            context.p6_output,
            context.sku_dict_lookup,
            context.recipe_names,
            context.store_id,
            p1_ingredient_lookup=context.p1_ingredient_lookup,
        )
        return context


# ============================================================================
# Public Orchestrator Interface
# ============================================================================


async def run_pipeline(
    store_id: str,
    connector: StoreConnector,
    firestore_client=None,
    force_refresh: bool = False,
    top_n: int = 20,
    top_k_p2: int = 20,
    top_k_p6: int = 10,
) -> List[BundleOutput]:
    """
    Run the full P1->P7 pipeline for a store using Chain of Responsibility.

    Args:
        store_id: store identifier
        connector: StoreConnector implementation
        firestore_client: optional Firestore client for weights/cache
        force_refresh: skip cache (for future Firestore integration)
        top_n: P1 batch count
        top_k_p2: P2 candidate count
        top_k_p6: P6 final bundle count
    """
    # Load reference data from DataRepository (singleton with lazy-load caching)
    repo = DataRepository.get()

    # Fetch store data
    batches_raw = connector.get_batches(store_id)

    # Convert ProductBatch objects to dicts for P1/P2 compatibility
    batches = []
    for b in batches_raw:
        if hasattr(b, "model_dump"):
            # Pydantic v2 model - convert to dict
            batch_dict = b.model_dump()
        elif hasattr(b, "dict"):
            # Pydantic v1 model - fallback
            batch_dict = b.dict()
        elif isinstance(b, dict):
            batch_dict = b
        else:
            batch_dict = vars(b)

        # Ensure remaining_qty_g is set for backward compatibility
        if "remaining_qty_g" not in batch_dict and "unit_count" in batch_dict and "pack_size_g" in batch_dict:
            batch_dict["remaining_qty_g"] = batch_dict["unit_count"] * batch_dict["pack_size_g"]

        batches.append(batch_dict)

    # Build sales history for all SKUs
    all_sku_ids = {b["sku_id"] for b in batches}
    sales_history = {}
    for sku_id in all_sku_ids:
        sales_history[sku_id] = connector.get_sales_history(store_id, sku_id)

    # Build pipeline context with all reference data and input
    context = PipelineContext(
        store_id=store_id,
        batches=batches,
        sales_history=sales_history,
        sku_lookup=repo.sku_lookup(),
        sku_dict_lookup=repo.sku_dict_lookup(),
        recipe_requirements=repo.recipe_requirements(),
        recipe_names=repo.recipe_names(),
        recipe_lookup=repo.recipe_lookup(),
        inverted_index=repo.inverted_index(),
        substitute_groups=repo.substitute_groups(),
        top_n=top_n,
        top_k_p2=top_k_p2,
        top_k_p6=top_k_p6,
    )

    # Execute pipeline chain (P1 → P2 → P3 → P5 → P6 → P7)
    chain = PipelineChain(
        stages=[
            P1_PriorityStage("P1_Priority"),
            P2_RetrievalStage("P2_Retrieval"),
            P3_FeasibilityStage("P3_Feasibility"),
            P5_WasteStage("P5_Waste"),
            P6_RankingStage("P6_Ranking"),
            P7_PricingStage("P7_Pricing"),
        ],
        allow_fallback=True,
    )

    context = chain.execute(context)

    # Cache P1 scores for /inventory to query without re-running the pipeline
    if context.p1_output:
        p1_cache.put(store_id, context.p1_output)

    # Return final bundles (or empty list if pipeline failed)
    return context.final_bundles or []
