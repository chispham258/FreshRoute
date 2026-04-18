# FreshRoute — AI Agents for Food Waste Reduction

FreshRoute is a dual-agent system for Vietnamese retail: the **B2B agent** recommends discounted recipe bundles that use expiring store inventory; the **Consumer agent** helps home cooks find recipes from what they have and generates shopping lists. Both agents sit on top of a deterministic fallback pipeline (P1→P7) that guarantees a valid response even when the LLM is unavailable.

---

## Architecture

```
Admin Portal / Customer Portal / AI Chat
              │
         FastAPI Router
         /     \
    B2B Agent   Consumer Agent        ← LangGraph custom StateGraph
        \           /
    Deterministic Pipeline (P1→P7)   ← fallback / finalization
              │
         DataRepository               ← singleton, 93 SKUs · 40 recipes
```

**Both agents are custom LangGraph `StateGraph`s** — not `create_react_agent`. This gives explicit routing and terminates the loop on a specific condition instead of relying on ReAct defaults.

**FPT AI Factory quirk:** The model often returns tool calls as plain text instead of structured `tool_calls`. Both agents carry a `_recover_tool_call_from_text` fallback that reconstructs a proper `AIMessage` using AST parsing (`ast.parse` for complex kwargs) so the ToolNode can execute normally.

---

## B2B Agent — Store Bundle Advisor

Triggered by `GET /api/admin/combos?storeId=<id>`.

1. Receives urgent inventory context (P1 scores injected into system prompt)
2. Calls `search_recipes_from_ingredients` to find recipe candidates
3. Calls `check_feasibility_and_substitute` per candidate (FEFO allocation)
4. Calls `finalize_bundles(recipe_ids, store_id)` → runs P5→P6→P7 deterministically
5. Graph terminates immediately after `finalize_bundles` (custom conditional edge)

Fallback: if agent fails, deterministic pipeline runs the full P1→P7 chain instead.

**Tools:**

| Tool | Purpose |
| --- | --- |
| `search_recipes_from_ingredients` | Find recipes weighted by ingredient urgency |
| `check_feasibility_and_substitute` | FEFO allocation + ontology substitution |
| `query_ontology` | Ingredient substitute lookup |
| `finalize_bundles` | Bridge to P5→P6→P7 pipeline, returns `List[BundleOutput]` |

---

## Consumer Agent — Home Cooking Assistant

Triggered by `POST /consumer/chat`.

Two modes, same agent:

**Discovery:** "I have thịt heo, trứng gà, hành tây — what should I cook?"

1. `resolve_ingredient_names` → canonical IDs
2. `find_recipes_for_consumer(available, urgent=[], allergies=[...])` → scored recipes
3. API response includes `recipe_suggestions` array (expand/collapse cards in UI)
4. User picks dish → `get_remaining_ingredients` → `shopping_list` in response

**Shopping:** "I want to make phở — what do I need to buy?"

1. `get_recipe_by_name` (fuzzy match)
2. `resolve_ingredient_names` on what user has
3. `get_remaining_ingredients(recipe_id, available_ids)` → shopping list with quantities + price

**Allergy handling:** When user says "tôi dị ứng X", agent calls `note_allergy(allergy_names=["X"])` immediately. This resolves and records allergen IDs as a `ToolMessage` in conversation history, so subsequent `find_recipes_for_consumer` calls receive `allergies=[...]` reliably across turns.

**Tools:**

| Tool | Mode |
| --- | --- |
| `resolve_ingredient_names` | Both |
| `find_recipes_for_consumer` | Discovery |
| `adjust_recipe_for_user` | Discovery |
| `get_recipe_by_name` | Shopping |
| `get_remaining_ingredients` | Shopping |
| `get_ingredient_suggestions` | Shopping |
| `query_ontology` | Both |
| `note_allergy` | Both |

---

## Deterministic Pipeline (P1→P7)

Runs as primary path for B2B (via `finalize_bundles`) and as fallback when agent fails.

| Stage | Purpose | Key Algorithm |
| --- | --- | --- |
| P1 Priority | Score each batch by expiry risk | `priority = w_e·exp(-λ·days) + w_s·sigmoid(supply_ratio) + w_d·(1-sell_through)` |
| P2 Retrieval | Match urgent ingredients → recipe candidates | `score = max_urgency + 0.3·Σ(other_urgencies)` |
| P3 Feasibility | FEFO allocation per ingredient, substitution | packet-based `allocate_fefo()`, completeness ≥ 0.7 |
| P5 Waste | Score value of urgent inventory rescued | `Σ(priority · cost_per_g · qty_taken_g)` |
| P6 Ranking | Multi-objective final score | `w1·urgency + w2·completeness + w3·waste − penalties` |
| P7 Pricing | Dynamic discount respecting margin floor | `discount = min(0.05 + 0.25·waste_norm, 0.30)`, margin-adjusted |

**FEFO strategies:** `strict` (ceil — guarantee coverage), `approx` (floor — minimize waste), `best` (strict first, fallback to approx if deviation > 25%).

---

## Quick Start

### Requirements

- Python 3.13+, [uv](https://docs.astral.sh/uv/)
- Node.js 18+
- FPT AI Factory API key (agents only; pipeline runs without it)

### Backend

```bash
uv sync
cp .env.example .env          # add OPENAI_API_KEY=<fpt-key>
uvicorn app.main:app --reload --port 8000
```

Swagger docs: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend && npm install && npm run dev
```

App: <http://localhost:3000>

### Docker

```bash
docker-compose up
```

### Tests

```bash
python -m pytest tests/ -v    # 85+ passing
```

---

## API Reference

### Admin / B2B

```bash
# AI-driven bundles (B2B agent → P5-P7 finalization)
GET /api/admin/combos?storeId=BHX-HCM001&limit=10

# Items nearing expiry (P1 scores)
GET /api/admin/inventory?storeId=BHX-HCM001

# Accept / reject a bundle suggestion
POST /api/admin/combos/{id}/accept
POST /api/admin/combos/{id}/reject
```

### Consumer

```bash
# Multi-turn cooking assistant (stateful by thread_id)
POST /consumer/chat
# body: { message, thread_id, allergies? }
# response: { reply, shopping_list?, recipe_suggestions? }

# One-shot suggestion (stateless)
POST /consumer/suggest
# body: { ingredients: [...], top_k: 3 }

# Combos for customer shopping portal
GET /consumer/api/customer/combos?storeId=BHX-HCM001
```

### Direct Pipeline (no LLM)

```bash
GET /bundles/BHX-HCM001            # deterministic, fast
GET /bundles/BHX-HCM001?agent=true # B2B agent path
```

---

## Project Structure

```
app/
├── agent/
│   ├── b2b/             graph.py · tools.py · prompt.py
│   ├── consumer/        graph.py · tools.py · prompt.py · state.py
│   ├── shared/          tool_factory.py · ontology.py
│   └── tools.py         shared tool implementations
├── core/
│   ├── pipeline/        p1–p7, orchestrator, base, p1_cache
│   ├── engine/          allocation.py · waste.py
│   ├── data/            repository.py · skus.py · recipes.py · *.json
│   └── models/          bundle.py · inventory.py · recipe.py
├── api/                 bundles.py · admin.py · consumer.py · health.py
├── integrations/        llm.py (FPTChatOpenAI) · connectors/ · db/
└── main.py

frontend/src/
├── app/
│   ├── admin/page.js
│   └── customer/
│       ├── page.js · cart/page.js · ai-chat/page.js
└── lib/
    ├── adminApi.js · customerApi.js · cart.js · currency.js
```

---

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | required | FPT AI Factory key |
| `OPENAI_MODEL` | `gpt-oss-120b` | LLM model ID |
| `TEMPERATURE` | `0.1` | Sampling temperature |
| `DEFAULT_CONNECTOR` | `mock` | `mock` (JSON fixtures) or `postgres` |

---

## Data

- **93 SKUs** across fresh meat, seafood, produce, dairy, condiments, dry goods
- **40 Vietnamese recipes** (Pho, Canh chua, Bun bo Hue, …)
- **178 ingredient aliases** for Vietnamese name resolution
- **29 substitution groups** in ontology
- **5 urgency decay categories** with λ ranging from 0.08 (processed) to 0.60 (fresh seafood)

---

**Built at GDSC Hackathon 2026 | Team: FreshRoute**
