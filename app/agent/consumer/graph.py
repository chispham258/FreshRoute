"""
LangGraph Consumer Home Cooking Agent (Feature 2).

Builds a multi-turn ReAct agent using create_react_agent with:
  - FPT AI Factory as the LLM (OpenAI-compatible API)
  - FPTChatOpenAI wrapper for proper tool response formatting
  - Consumer-specific tools (resolve names, find recipes, adjust, ontology)
  - MemorySaver checkpointer for multi-turn conversation state
  - Consumer system prompt emphasizing urgent ingredients + allergy safety
"""

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.agent.consumer.prompt import CONSUMER_SYSTEM_PROMPT
from app.agent.consumer.tools import consumer_langchain_tools
from app.integrations.llm import get_llm


# In-memory checkpointer for multi-turn conversation.
# In production, swap for a persistent checkpointer (e.g. PostgresSaver).
memory = MemorySaver()


def build_consumer_agent():
    """
    Build and return the compiled consumer ReAct agent.

    The agent supports multi-turn conversations via the MemorySaver
    checkpointer — each thread_id maintains its own conversation history.
    """
    llm = get_llm()
    agent = create_react_agent(
        model=llm,
        tools=consumer_langchain_tools,
        state_modifier=CONSUMER_SYSTEM_PROMPT,
        checkpointer=memory,
        debug=False,
    )
    return agent


# Lazy singleton — built on first use so import doesn't require API key
_consumer_agent = None


def get_consumer_agent():
    """Get or create the consumer agent singleton."""
    global _consumer_agent
    if _consumer_agent is None:
        _consumer_agent = build_consumer_agent()
    return _consumer_agent


async def chat(
    message: str,
    thread_id: str,
    user_context: dict | None = None,
) -> str:
    """
    Send a message to the consumer agent and get a response.

    Args:
        message: The user's message in natural language (Vietnamese).
        thread_id: Unique conversation thread ID for multi-turn state.
        user_context: Optional dict with {user_id, allergies, dietary_preferences}
                      to inject into the first message of a conversation.

    Returns:
        The agent's text response.
    """
    agent = get_consumer_agent()

    # Build the user message, optionally prepending context
    content = message
    if user_context:
        context_parts = []
        if user_context.get("allergies"):
            allergies_str = ", ".join(user_context["allergies"])
            context_parts.append(f"[Dị ứng: {allergies_str}]")
        if user_context.get("dietary_preferences"):
            prefs_str = ", ".join(user_context["dietary_preferences"])
            context_parts.append(f"[Chế độ ăn: {prefs_str}]")
        if context_parts:
            content = " ".join(context_parts) + "\n" + message

    config = {"configurable": {"thread_id": thread_id}}
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content=content)]},
        config=config,
    )

    # Extract the last AI message text
    ai_messages = [
        m for m in response["messages"]
        if hasattr(m, "type") and m.type == "ai" and m.content
    ]
    if ai_messages:
        return ai_messages[-1].content

    return "Xin lỗi, tôi không thể xử lý yêu cầu này. Bạn thử lại nhé!"


async def suggest(
    ingredients: list[str],
    allergies: list[str] | None = None,
    top_k: int = 3,
) -> dict:
    """
    One-shot suggestion: given a list of ingredient names, return recipe suggestions.

    This is a stateless call — no multi-turn conversation.
    It uses the core tools directly without going through the LLM,
    for faster and more deterministic results.

    Args:
        ingredients: List of ingredient names in Vietnamese (e.g. ["thịt heo", "cà chua"]).
        allergies: Optional list of ingredient names the user is allergic to.
        top_k: Number of recipe suggestions to return.

    Returns:
        Dict with resolved ingredients, urgent items, and ranked recipes.
    """
    from app.agent.tools import (
        adjust_recipe_for_user as _adjust,
        find_recipes_for_consumer as _find,
        get_user_urgent_ingredients as _urgent,
        resolve_ingredient_names as _resolve,
    )

    # Resolve natural names → IDs
    resolved = _resolve(ingredients)
    resolved_ids = [r["ingredient_id"] for r in resolved if r["resolved"]]
    unresolved = [r["input"] for r in resolved if not r["resolved"]]

    # Build inventory-like dicts (no expiry info for one-shot — treat all as non-urgent)
    available = [{"ingredient_id": ing_id, "quantity_g": 500, "expiry_days": 99}
                 for ing_id in resolved_ids]

    # No urgent items in one-shot mode (user didn't provide expiry info)
    urgent = _urgent(available, threshold_days=3)

    # Resolve allergy names → IDs
    allergy_ids = []
    if allergies:
        allergy_resolved = _resolve(allergies)
        allergy_ids = [r["ingredient_id"] for r in allergy_resolved if r["resolved"]]

    # Find recipes
    recipes = _find(available, urgent, allergy_ids, top_k)

    # Adjust top recipes
    adjusted_recipes = []
    for recipe in recipes:
        adjusted = _adjust(recipe, available, allergy_ids)
        adjusted_recipes.append(adjusted)

    return {
        "resolved_ingredients": resolved,
        "unresolved_ingredients": unresolved,
        "allergy_ids": allergy_ids,
        "suggestions": adjusted_recipes,
    }
