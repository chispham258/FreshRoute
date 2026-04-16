"""
Shared utilities for agents — tool factory, LLM wrapper, ontology.
"""

from app.agent.shared.tool_factory import make_tool
from app.agent.shared.ontology import query_ontology

__all__ = ["make_tool", "query_ontology"]
