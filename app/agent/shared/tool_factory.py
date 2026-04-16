"""
Tool Factory — Auto-wraps plain Python functions as LangChain @tools.

Eliminates boilerplate for JSON serialization and error handling.
"""

import json
import functools
from typing import Callable, Any
from langchain_core.tools import tool


def make_tool(
    fn: Callable,
    serialize_output: bool = True,
    name: str | None = None,
    description: str | None = None,
) -> Callable:
    """
    Wrap a plain Python function as a LangChain @tool.

    Args:
        fn: Function to wrap
        serialize_output: If True (default), convert output to JSON string
        name: Override tool name (defaults to fn.__name__)
        description: Override tool description (defaults to fn.__doc__)

    Returns:
        LangChain @tool-decorated function that can be used in agents
    """

    @tool
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> str | Any:
        """Execute the tool and optionally serialize output."""
        try:
            result = fn(*args, **kwargs)

            if serialize_output:
                # Convert to JSON for LLM compatibility
                return json.dumps(result, ensure_ascii=False, default=str)
            else:
                return result

        except Exception as e:
            # Return error as JSON
            error_response = {
                "error": str(e),
                "type": type(e).__name__,
            }
            return json.dumps(error_response, ensure_ascii=False)

    # Override name and description if provided
    if name:
        wrapper.name = name
    if description:
        wrapper.description = description

    return wrapper
