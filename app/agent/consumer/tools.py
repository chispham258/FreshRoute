"""
LangChain @tool wrappers for the Consumer Home Cooking Agent.

Uses tool_factory to reduce boilerplate.
"""

from app.agent.tools import (
    resolve_ingredient_names as _resolve,
    get_user_urgent_ingredients as _urgent,
    find_recipes_for_consumer as _find,
    adjust_recipe_for_user as _adjust,
    get_recipe_by_name as _get_recipe_by_name,
    get_remaining_ingredients as _get_remaining_ingredients,
    get_ingredient_suggestions as _get_ingredient_suggestions,
)
from app.agent.shared.tool_factory import make_tool
from app.agent.shared.ontology import query_ontology as _query_ontology


# Discovery mode tools
resolve_ingredient_names = make_tool(
    _resolve,
    description="Resolve Vietnamese ingredient names to system IDs."
)

get_user_urgent_ingredients = make_tool(
    _urgent,
    description="Filter user inventory to items expiring within threshold_days."
)

find_recipes_for_consumer = make_tool(
    _find,
    description="Find and score recipes for a consumer based on their ingredients."
)

adjust_recipe_for_user = make_tool(
    _adjust,
    description="Adjust a recipe for a user's specific inventory and allergies."
)

# Shopping mode tools
get_recipe_by_name = make_tool(
    _get_recipe_by_name,
    description="Find a recipe by Vietnamese name (fuzzy match). Use when user wants to cook a specific dish."
)

get_remaining_ingredients = make_tool(
    _get_remaining_ingredients,
    description="Compute what ingredients user still needs to buy for a recipe given what they already have."
)

get_ingredient_suggestions = make_tool(
    _get_ingredient_suggestions,
    description="Get substitute suggestions for missing ingredients in a recipe the user wants to cook."
)

# Shared
query_ontology = make_tool(
    _query_ontology,
    description="Look up ingredient relationships in the Vietnamese food ontology."
)


# All consumer tools for LangGraph agent registration
consumer_langchain_tools = [
    # Discovery mode: "I don't know what to cook"
    resolve_ingredient_names,
    get_user_urgent_ingredients,
    find_recipes_for_consumer,
    adjust_recipe_for_user,
    # Shopping mode: "I want to cook this specific dish"
    get_recipe_by_name,
    get_remaining_ingredients,
    get_ingredient_suggestions,
    # Shared
    query_ontology,
]
