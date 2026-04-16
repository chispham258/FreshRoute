"""
Pipeline Base Classes — Chain of Responsibility pattern for P1-P7 stages.

Each stage receives a PipelineContext, processes it, and passes enriched context to the next stage.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PipelineContext:
    """Immutable context passed through the pipeline chain.

    Holds input parameters, intermediate results, and final output.
    Each stage adds its output fields without modifying prior stages' data.
    """
    # Input parameters
    store_id: str
    batches: List[Dict[str, Any]]
    sales_history: Dict[str, List[Dict[str, Any]]]

    # Reference data
    sku_lookup: Dict[str, Any]
    sku_dict_lookup: Dict[str, Dict[str, Any]]
    recipe_requirements: Dict[str, List[str]]
    recipe_names: Dict[str, str]
    recipe_lookup: Dict[str, Dict[str, Any]]
    inverted_index: Dict[str, List[str]]
    substitute_groups: Dict[str, List[str]]

    # Pagination/control
    top_n: int = 20
    top_k_p2: int = 20
    top_k_p6: int = 10

    # Pipeline stage outputs
    p1_output: Optional[List[Dict[str, Any]]] = None
    p2_output: Optional[List[Dict[str, Any]]] = None
    p3_output: Optional[List[Dict[str, Any]]] = None
    p5_output: Optional[List[Dict[str, Any]]] = None
    p6_output: Optional[List[Dict[str, Any]]] = None
    final_bundles: Optional[List[Dict[str, Any]]] = None

    # P1 lookup for enrichment: ingredient_id -> urgency_flag
    p1_ingredient_lookup: Dict[str, str] = field(default_factory=dict)

    # Error tracking
    errors: List[str] = field(default_factory=list)


class PipelineStage(ABC):
    """Abstract base class for pipeline stages.

    Implements Chain of Responsibility: each stage processes context and yields it to next.
    Supports optional error recovery (fallback to previous stage output).
    """

    def __init__(self, name: str):
        """Initialize stage with a human-readable name for logging.

        Args:
            name: Stage identifier (e.g., "P1_Priority", "P6_Ranking")
        """
        self.name = name

    @abstractmethod
    def run(self, context: PipelineContext) -> PipelineContext:
        """Process pipeline context and return enriched context.

        Args:
            context: Immutable context from previous stage

        Returns:
            Updated context with this stage's output filled in
        """
        pass


class PipelineChain:
    """Executes a chain of PipelineStage instances in sequence.

    Handles errors: if a stage fails, logs error and optionally falls back to
    the previous stage's output (configurable per chain).
    """

    def __init__(self, stages: List[PipelineStage], allow_fallback: bool = True):
        """Initialize chain with ordered stages.

        Args:
            stages: Ordered list of PipelineStage instances
            allow_fallback: If True, continue pipeline on stage failure using prior output
        """
        self.stages = stages
        self.allow_fallback = allow_fallback

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute all stages in order, passing context through each.

        Args:
            context: Initial pipeline context

        Returns:
            Final context with all pipeline outputs
        """
        for stage in self.stages:
            try:
                context = stage.run(context)
            except Exception as e:
                error_msg = f"{stage.name} failed: {str(e)}"
                context.errors.append(error_msg)

                if not self.allow_fallback:
                    raise

        return context
