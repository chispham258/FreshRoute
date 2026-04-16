"""
Base agent state for LangGraph agents.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Base state for all LangGraph agents — holds the conversation message list."""
    messages: Annotated[list, add_messages]
