"""
LangGraph B2B Store Bundle Agent.

Uses a custom StateGraph (not create_react_agent) so we can add a
conditional edge that terminates the loop as soon as `finalize_bundles`
completes — preventing the model from calling it repeatedly.

Flow:
    START → agent → (tool call?) → tools → (finalize_bundles?) → END
                                         ↑_________________________|
                                         (continue if not finalize_bundles)
"""

import json
import logging
import uuid
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

from app.agent.b2b.prompt import B2B_SYSTEM_PROMPT
from app.agent.b2b.tools import b2b_langchain_tools
from app.integrations.llm import get_llm
from app.agent.tools import get_urgent_inventory

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _parse_python_call_args(text: str) -> dict | None:
    """Parse Python-style kwargs string using the AST.

    Handles both double- and single-quoted strings, nested dicts/lists, and
    multiline calls — far more robust than regex-based JSON conversion.
    """
    import ast
    try:
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
      1. Raw JSON dict: {"recipe_ids": [...], "store_id": "...", "top_k": 10}
      2. Python call syntax: finalize_bundles(recipe_ids=[...], store_id="...", top_k=10)
         (handles both single- and double-quoted string values via AST)

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

                            # Fallback: regex-based JSON conversion (simple cases only)
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
            logger.warning(f"[b2b][fallback] Recovering tool call '{matched_tool.name}' from text content")
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


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def _build_b2b_graph():
    llm_with_tools = get_llm().bind_tools(b2b_langchain_tools)
    tool_node = ToolNode(b2b_langchain_tools)

    def call_agent(state: MessagesState):
        """LLM node — prepends system message on every call to prevent drift."""
        messages = [SystemMessage(content=B2B_SYSTEM_PROMPT)] + state["messages"]

        response = llm_with_tools.invoke(messages)

        # Log LLM reasoning (text content before tool calls)
        if hasattr(response, "content") and response.content:
            logger.debug(f"[llm_think] {str(response.content)[:500]}")

        # Fallback: FPT model may return tool args as JSON text instead of tool_calls
        if not getattr(response, "tool_calls", None):
            response = _recover_tool_call_from_text(response, b2b_langchain_tools)

        if getattr(response, "tool_calls", None):
            for tc in response.tool_calls:
                logger.info(f"[llm_calls] {tc.get('name')}  args_keys={list(tc.get('args', {}).keys())}")

        return {"messages": [response]}

    def route_after_agent(state: MessagesState) -> str:
        """Route to tools if there are pending tool calls, else END."""
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return END

    def route_after_tools(state: MessagesState) -> str:
        """IMPROVED: Check the actual ToolMessage (more reliable than walking AI messages)."""
        last_msg = state["messages"][-1]
        if isinstance(last_msg, ToolMessage) and last_msg.name == "finalize_bundles":
            logger.info("finalize_bundles completed — terminating agent loop")
            return END
        return "agent"

    # def route_after_tools(state: MessagesState) -> str:
    #     """
    #     After executing tools, check if finalize_bundles was just called.
    #     If yes → END (results are in the tool response, no further steps needed).
    #     If no  → back to agent.
    #     """
    #     messages = state["messages"]
    #     # Walk backwards to find the AI message that triggered the tool calls
    #     for msg in reversed(messages):
    #         if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
    #             for tc in msg.tool_calls:
    #                 tool_name = tc.get("name")
    #                 args_preview = json.dumps(tc.get("args", {}), ensure_ascii=False)[:300]
    #                 logger.debug(f"[tool_call] {tool_name}({args_preview})")
    #                 if tool_name == "finalize_bundles":
    #                     logger.info(f"[finalize_bundles] args: {json.dumps(tc.get('args', {}), ensure_ascii=False)}")
    #                     logger.info("finalize_bundles completed — terminating agent loop")
    #                     return END
    #             break  # found the last AI message, no finalize_bundles → continue
    #     return "agent"

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_agent)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
    graph.add_conditional_edges("tools", route_after_tools, {"agent": "agent", END: END})

    return graph.compile()


# Lazy singleton
_b2b_graph = None


def get_b2b_agent():
    global _b2b_graph
    if _b2b_graph is None:
        _b2b_graph = _build_b2b_graph()
    return _b2b_graph


# Backward compatibility alias
build_b2b_agent = get_b2b_agent


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_b2b_agent(store_id: str, top_k: int = 10) -> list:
    """
    Run the B2B agent for a store.

    The agent receives the pre-computed P1 urgent inventory as context and
    calls tools to find feasible recipes, check ontology-based substitutes,
    then calls finalize_bundles once to get P5-P7 scored bundles.

    Returns a list of bundle dicts, or [] on error.
    """
    logger.info(f"=== Starting B2B Agent for store {store_id}, top_k={top_k} ===")

    # Pre-compute P1 urgent inventory (fast, deterministic — no LLM needed)
    urgent_batches = get_urgent_inventory(store_id, top_n=25)
    logger.info(f"Found {len(urgent_batches)} urgent batches")

    def _urgency_flag_from_score(priority_score: float) -> str:
        """Determine urgency tier based on priority_score (0-1)."""
        if priority_score >= 0.80:
            return "CRITICAL"
        if priority_score >= 0.65:
            return "HIGH"
        if priority_score >= 0.50:
            return "MEDIUM"
        return "WATCH"

    urgent_context = [
        {
            "batch_id": b.get("batch_id"),
            "ingredient_id": b["ingredient_id"],
            "expiry_days": b["expiry_days"],
            "remaining_qty_g": round(b.get("unit_count", 1) * b.get("pack_size_g", 500), 1),
            "priority_score": round(b.get("priority_score", 0), 4),
            "urgency_flag": _urgency_flag_from_score(b.get("priority_score", 0)),
        }
        for b in urgent_batches[:30]
    ]

    # Build urgency dict for direct injection into search_recipes_from_ingredients
    ingredient_urgency = {b["ingredient_id"]: b["priority_score"] for b in urgent_context}

    prompt = f"""
        Cửa hàng: {store_id}
        Mục tiêu: Tạo TỐI ĐA {top_k} bundle giảm lãng phí thực phẩm.

        Danh sách urgent inventory (P1 đã tính sẵn):
        {json.dumps(urgent_context, ensure_ascii=False, indent=2)}

        ingredient_urgency dict (dùng ngay cho search_recipes_from_ingredients):
        {json.dumps(ingredient_urgency, ensure_ascii=False)}

        STRICT INSTRUCTION — BẮT ĐẦU NGAY:
        Bạn PHẢI gọi tool đầu tiên là search_recipes_from_ingredients với:
        - ingredient_ids: danh sách tất cả ingredient_id ở trên
        - ingredient_urgency: dict ở trên (ingredient_id → priority_score)

        Không được trả lời bằng văn bản. Chỉ được gọi tool.
        Bắt đầu ngay theo quy trình: search → check_feasibility → (query_ontology nếu cần) → finalize_bundles.
    """

    try:
        graph = get_b2b_agent()
        logger.debug("B2B graph initialized")

        response = await graph.ainvoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"recursion_limit": 80},
        )
        logger.info(f"Agent completed with {len(response.get('messages', []))} messages")

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        return []

    messages = response.get("messages", [])

    # Log tool calls sequence
    tool_calls_sequence = []
    for m in messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tool_calls_sequence.append(tc.get("name"))
    logger.info(f"Tool calls: {tool_calls_sequence}")

    # -----------------------------------------------------------------------
    # Extract finalize_bundles result from tool response messages
    # -----------------------------------------------------------------------
    finalize_called = "finalize_bundles" in tool_calls_sequence
    bundles = []

    # Search backwards for the ToolMessage produced by finalize_bundles.
    # Walking in reverse is safe even when multiple tools fired in one AIMessage turn.
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "finalize_bundles":
            raw = getattr(msg, "content", "")
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(parsed, list):
                    bundles = parsed
                else:
                    logger.warning(f"finalize_bundles returned non-list: {str(raw)[:200]}")
            except Exception:
                logger.warning("Could not parse finalize_bundles response")
            break
    logger.info(f"finalize_bundles_called={finalize_called}, bundles={len(bundles)}")
    return bundles




