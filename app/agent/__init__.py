"""
FreshRoute Agent Module — LangGraph agents for B2B and Consumer use cases.

Exports:
- B2B Agent: build_b2b_agent(), run_b2b_agent()
- Consumer Agent: build_consumer_agent(), chat(), suggest()
- Shared tools & utilities: tools, tool_factory, ontology, llm
"""

# Shared utilities
from app.integrations.llm import get_llm, FPTChatOpenAI
from app.agent.shared.tool_factory import make_tool
from app.agent.shared.ontology import query_ontology
from app.agent.state import AgentState

# B2B Agent
from app.agent.b2b import build_b2b_agent, b2b_langchain_tools, B2B_SYSTEM_PROMPT

# Consumer Agent
from app.agent.consumer import build_consumer_agent, chat, suggest, consumer_langchain_tools, CONSUMER_SYSTEM_PROMPT, ConsumerState

__all__ = [
    # Shared
    "get_llm",
    "FPTChatOpenAI",
    "make_tool",
    "query_ontology",
    "AgentState",
    # B2B
    "build_b2b_agent",
    "b2b_langchain_tools",
    "B2B_SYSTEM_PROMPT",
    # Consumer
    "build_consumer_agent",
    "chat",
    "suggest",
    "consumer_langchain_tools",
    "CONSUMER_SYSTEM_PROMPT",
    "ConsumerState",
]
