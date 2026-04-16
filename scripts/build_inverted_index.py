"""
Build ingredient -> recipe inverted index from recipe fixtures.

Run: python -m scripts.build_inverted_index
"""

import json
from collections import defaultdict
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def build_index(recipes: list) -> dict:
    index = defaultdict(list)
    for recipe in recipes:
        for ing in recipe.get("ingredients", []):
            index[ing["ingredient_id"]].append(recipe["recipe_id"])
    return dict(index)


def main():
    with open(FIXTURES_DIR / "recipes.json") as f:
        recipes = json.load(f)

    index = build_index(recipes)

    output_path = FIXTURES_DIR / "inverted_index.json"
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"Built inverted index: {len(index)} ingredients -> recipes")
    for ing_id, rids in sorted(index.items()):
        print(f"  {ing_id}: {rids}")


if __name__ == "__main__":
    main()
