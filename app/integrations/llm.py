"""
LLM Integration Layer — FPT AI Factory (OpenAI-compatible API).

Exports FPTChatOpenAI wrapper and factory function for both B2B and Consumer agents.
"""

import json
from langchain_openai import ChatOpenAI
from app.config import get_settings


class FPTChatOpenAI(ChatOpenAI):
    """Wrapper to fix tool call format for FPT AI Factory.

    FPT AI requires tool response messages to have:
    - tool_call_id (to reference the assistant's tool call)
    - name (actual function name that was called)
    - content (string, result of tool execution)

    This wrapper extracts the real tool name from assistant messages
    and fills in missing fields in tool responses.
    """

    def _get_request_payload(self, input_, stop=None, **kwargs):
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)

        messages = payload.get("messages", [])

        # Step 1: Build mapping of tool_call_id -> actual_tool_name
        # by scanning assistant messages
        tool_names = {}
        for m in messages:
            if m.get("role") == "assistant" and m.get("tool_calls"):
                for tool_call in m["tool_calls"]:
                    tool_id = tool_call.get("id")
                    # Handle both OpenAI SDK format and LangChain format
                    tool_name = (
                        tool_call.get("name") or  # LangChain format
                        tool_call.get("function", {}).get("name")  # OpenAI SDK format
                    )
                    if tool_id and tool_name:
                        tool_names[tool_id] = tool_name

        # Step 2: Fix tool response messages
        for m in messages:
            if m.get("role") == "tool":
                tool_call_id = m.get("tool_call_id")

                # CRITICAL: Add the 'name' key that FPT AI requires
                if tool_call_id in tool_names:
                    # Use the actual tool name from mapping
                    m["name"] = tool_names[tool_call_id]
                elif not m.get("name"):
                    # Fallback if we can't find the mapping
                    # This shouldn't happen in normal flow
                    m["name"] = "tool"

                # Ensure content is always a string
                if not isinstance(m.get("content"), str):
                    m["content"] = json.dumps(m.get("content", ""), ensure_ascii=False)

                # Ensure tool_call_id exists
                if not tool_call_id:
                    m["tool_call_id"] = "auto_id"

        return payload


def get_llm() -> FPTChatOpenAI:
    """Get LLM instance (FPT AI Factory via OpenAI-compatible API).

    NOTE: Not cached — settings may change via env vars, and we want to pick
    up OPENAI_MODEL changes immediately without restart.
    """
    settings = get_settings()

    return FPTChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        temperature=settings.TEMPERATURE,
        base_url="https://mkp-api.fptcloud.com/v1",
    )
