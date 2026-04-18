"""
LangGraph Consumer Home Cooking Agent (Feature 2).

Uses a custom StateGraph (not create_react_agent) so we can add
tool-call recovery for FPT AI Factory — the model sometimes returns
tool arguments as plain JSON text instead of proper tool_calls.

Features:
  - FPT AI Factory as the LLM (OpenAI-compatible API)
  - FPTChatOpenAI wrapper for proper tool response formatting
  - Consumer-specific tools (resolve names, find recipes, adjust, ontology)
  - MemorySaver checkpointer for multi-turn conversation state
  - Tool-call recovery from text (same mechanism as B2B agent)
"""

import json
import logging
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

from app.agent.consumer.prompt import CONSUMER_SYSTEM_PROMPT
from app.agent.consumer.tools import consumer_langchain_tools
from app.integrations.llm import get_llm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# In-memory checkpointer for multi-turn conversation.
memory = MemorySaver()


def _extract_recipe_suggestions(messages: list) -> list | None:
    """Return enriched recipe suggestions from the last find_recipes_for_consumer tool result."""
    call_ids = set()
    for m in messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                if tc.get("name") == "find_recipes_for_consumer":
                    call_ids.add(tc.get("id"))

    if not call_ids:
        # Also try scanning ToolMessages directly by name (fallback for serialized state)
        for m in reversed(messages):
            if isinstance(m, ToolMessage) and getattr(m, "name", None) == "find_recipes_for_consumer":
                try:
                    content = json.loads(m.content) if isinstance(m.content, str) else m.content
                    if isinstance(content, list) and content:
                        logger.info(f"[consumer][extract] Found find_recipes ToolMessage by name, {len(content)} recipes")
                        return _enrich_suggestions(content)
                except Exception as exc:
                    logger.warning(f"[consumer][extract] Failed to parse ToolMessage by name: {exc}")
        logger.info("[consumer][extract] No find_recipes_for_consumer tool calls found in messages")
        return None

    logger.info(f"[consumer][extract] Found find_recipes call_ids: {call_ids}")
    for m in reversed(messages):
        if isinstance(m, ToolMessage) and m.tool_call_id in call_ids:
            try:
                content = json.loads(m.content) if isinstance(m.content, str) else m.content
                if isinstance(content, list):
                    logger.info(f"[consumer][extract] Enriching {len(content)} raw suggestions")
                    return _enrich_suggestions(content)
                else:
                    logger.warning(f"[consumer][extract] ToolMessage content is not a list: {type(content)}")
            except Exception as exc:
                logger.warning(f"[consumer][extract] Failed to parse ToolMessage content: {exc}")
    logger.info("[consumer][extract] No matching ToolMessage found for call_ids")
    return None


def _enrich_suggestions(raw: list) -> list:
    """Convert raw find_recipes_for_consumer output to per-ingredient display format."""
    from app.agent.tools import get_ingredient_display_name
    result = []
    for r in raw:
        try:
            user_ids = set(r.get("urgent_used", [])) | set(r.get("available_used", []))
            ingredients = [
                {
                    "name": get_ingredient_display_name(ing["ingredient_id"]),
                    "have": ing["ingredient_id"] in user_ids,
                    "optional": ing.get("is_optional", False),
                }
                for ing in r.get("ingredients", [])
            ]
            result.append({
                "recipe_id": r["recipe_id"],
                "name": r["name"],
                "score": r.get("score", 0),
                "ingredients": ingredients,
            })
        except Exception as exc:
            logger.warning(f"[consumer][enrich] Failed to enrich recipe {r.get('recipe_id', '?')}: {exc}")
    logger.info(f"[consumer][enrich] Enriched {len(result)} suggestions")
    return result


def _extract_shopping_list(messages: list) -> list | None:
    """Return the to_buy list from the last get_remaining_ingredients tool result."""
    call_ids = set()
    for m in messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                if tc.get("name") == "get_remaining_ingredients":
                    call_ids.add(tc.get("id"))
    if not call_ids:
        return None
    for m in reversed(messages):
        if isinstance(m, ToolMessage) and m.tool_call_id in call_ids:
            try:
                content = json.loads(m.content) if isinstance(m.content, str) else m.content
                if isinstance(content, dict) and content.get("to_buy"):
                    return content["to_buy"]
            except Exception:
                pass
    return None

# Maximum agent loop iterations to prevent infinite loops
MAX_ITERATIONS = 15


def _parse_python_call_args(text: str) -> dict | None:
    """
    Parse Python-style kwargs string using the AST.

    Handles both double- and single-quoted strings, nested dicts/lists, and
    multiline calls — far more robust than regex-based JSON conversion.

    Returns a dict of kwargs, or None on failure.
    """
    import ast
    try:
        # Wrap in a throwaway call so ast.parse can handle the kwargs
        tree = ast.parse(f"_f({text})", mode="eval")
        call = tree.body
        if not isinstance(call, ast.Call):
            return None
        result = {}
        for kw in call.keywords:
            result[kw.arg] = ast.literal_eval(kw.value)
        return result or None
    except Exception:
        return None


def _recover_tool_call_from_text(response, tools):
    """Fallback: FPT model may return tool args as JSON text instead of tool_calls.

    Handles two formats the model may produce:
      1. Raw JSON dict: {"user_inputs": ["thịt heo", ...]}
      2. Python call syntax: resolve_ingredient_names(user_inputs=["thịt heo", ...])
         (handles both single- and double-quoted string values)

    Reconstructs a proper AIMessage with tool_calls so the graph routes to ToolNode.
    """
    import re
    try:
        content = response.content
        if not isinstance(content, str):
            return response

        stripped = content.strip()
        args = None
        matched_tool = None

        # --- Format 1: JSON dict ---
        if stripped.startswith("{"):
            try:
                candidate = json.loads(stripped)
                if isinstance(candidate, dict):
                    for t in tools:
                        schema = t.args_schema.schema() if hasattr(t, "args_schema") else {}
                        required = set(schema.get("required", []))
                        if required and required.issubset(candidate.keys()):
                            args = candidate
                            matched_tool = t
                            break
            except Exception:
                pass

        # --- Format 2: Python call syntax  tool_name(key=val, ...) ---
        if args is None:
            m = re.match(r"^\s*(\w+)\s*\(", stripped)
            if m:
                call_name = m.group(1)
                for t in tools:
                    if t.name == call_name:
                        body_match = re.search(r"\((.*)\)\s*$", stripped, re.DOTALL)
                        if body_match:
                            body = body_match.group(1).strip()

                            # Try AST first (handles single/double quotes, nested structures)
                            candidate = _parse_python_call_args(body)

                            # Fallback: regex-based JSON conversion (simple cases)
                            if candidate is None:
                                json_body = re.sub(r'(\w+)\s*=\s*', r'"\1": ', body)
                                try:
                                    candidate = json.loads("{" + json_body + "}")
                                except Exception:
                                    pass

                            if isinstance(candidate, dict):
                                args = candidate
                                matched_tool = t
                        break

        if args is not None and matched_tool is not None:
            logger.warning(f"[consumer][fallback] Recovering tool call '{matched_tool.name}' from text")
            return AIMessage(
                content="",
                tool_calls=[{
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "name": matched_tool.name,
                    "args": args,
                    "type": "tool_call",
                }]
            )
    except Exception:
        pass
    return response


def _build_consumer_graph():
    llm_with_tools = get_llm().bind_tools(consumer_langchain_tools)
    tool_node = ToolNode(consumer_langchain_tools)

    def call_agent(state: MessagesState):
        """LLM node — prepends system message on every call."""
        messages = [SystemMessage(content=CONSUMER_SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)

        if hasattr(response, "content") and response.content:
            logger.debug(f"[consumer][llm] {str(response.content)[:300]}")

        # Fallback: recover tool calls from text content
        if not getattr(response, "tool_calls", None):
            response = _recover_tool_call_from_text(response, consumer_langchain_tools)

        if getattr(response, "tool_calls", None):
            for tc in response.tool_calls:
                logger.info(f"[consumer][tool_call] {tc.get('name')}  args_keys={list(tc.get('args', {}).keys())}")

        return {"messages": [response]}

    def route_after_agent(state: MessagesState) -> str:
        """Route to tools if there are pending tool calls, else END."""
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        # No tool calls = final text response → done
        return END

    def route_after_tools(state: MessagesState) -> str:
        """Always loop back to agent for next reasoning step."""
        # Guard against infinite loops
        ai_count = sum(1 for m in state["messages"] if isinstance(m, AIMessage))
        if ai_count >= MAX_ITERATIONS:
            logger.warning(f"[consumer] Hit max iterations ({MAX_ITERATIONS}), stopping")
            return END
        return "agent"

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_agent)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
    graph.add_conditional_edges("tools", route_after_tools, {"agent": "agent", END: END})

    return graph.compile(checkpointer=memory)


# Lazy singleton
_consumer_agent = None


def get_consumer_agent():
    """Get or create the consumer agent singleton."""
    global _consumer_agent
    if _consumer_agent is None:
        _consumer_agent = _build_consumer_graph()
    return _consumer_agent


# Backward compatibility alias
build_consumer_agent = get_consumer_agent


async def chat(
    message: str,
    thread_id: str,
    user_context: dict | None = None,
) -> tuple[str, list | None, list | None]:
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

    # Extract the final AI response text.
    # Priority: last AI message without tool_calls (pure text response),
    # then fall back to last AI message with any content.
    messages = response["messages"]
    shopping_list = _extract_shopping_list(messages)
    recipe_suggestions = _extract_recipe_suggestions(messages)
    logger.info(f"[consumer][chat] shopping_list={shopping_list is not None}, recipe_suggestions={recipe_suggestions is not None} ({len(recipe_suggestions) if recipe_suggestions else 0} items)")

    pure_text = [
        m for m in messages
        if isinstance(m, AIMessage) and m.content and not getattr(m, "tool_calls", None)
    ]
    if pure_text:
        return pure_text[-1].content, shopping_list, recipe_suggestions

    # Fallback: any AI message with content (even if it also had tool_calls)
    any_content = [
        m for m in messages
        if isinstance(m, AIMessage) and m.content
    ]
    if any_content:
        return any_content[-1].content, shopping_list, recipe_suggestions

    logger.warning("[consumer] No AI message with content found in response")
    return "Xin lỗi, tôi không thể xử lý yêu cầu này. Bạn thử lại nhé!", None, None


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
