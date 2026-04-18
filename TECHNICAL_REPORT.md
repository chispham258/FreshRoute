# FreshRoute — Technical Architecture Report

**Stack:** Python 3.13 · FastAPI · LangGraph · FPT AI Factory · Next.js · Pydantic v2

**Date:** April 2026

**Theme:** Agent of Change — Autonomous AI systems making real-world decisions

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Agent Architecture](#2-agent-architecture)
3. [B2B Agent](#3-b2b-agent)
4. [Consumer Agent](#4-consumer-agent)
5. [Deterministic Pipeline (P1–P7)](#5-deterministic-pipeline-p1p7)
6. [FEFO Allocation Engine](#6-fefo-allocation-engine)
7. [Ingredient Ontology](#7-ingredient-ontology)
8. [Data Layer](#8-data-layer)
9. [Frontend Integration](#9-frontend-integration)
10. [Testing](#10-testing)
11. [Deployment](#11-deployment)

---

## 1. System Overview

FreshRoute reduces food waste in Vietnamese retail by intelligently matching expiring store inventory with recipes, packaging them as discounted bundles, and helping home cooks discover meals from what they already have.

**Three interlocking layers:**

- **B2B Agent** — analyzes store inventory, reasons about recipe feasibility, selects bundles, hands off to deterministic pricing
- **Consumer Agent** — multi-turn conversational assistant for home cooks (recipe discovery + shopping list generation)
- **P1→P7 Pipeline** — deterministic fallback and finalization stage; always available, no LLM required

**Data:**

- 93 SKUs (fresh meat, seafood, produce, dairy, condiments, dry goods)
- 40 Vietnamese recipes
- 178 ingredient aliases for Vietnamese name resolution
- 29 substitution groups in ingredient ontology
- 5 urgency decay categories

---

## 2. Agent Architecture

### 2.1 Custom StateGraph (both agents)

Both agents use a custom LangGraph `StateGraph`, not the prebuilt `create_react_agent`. This provides:

- **Explicit routing:** conditional edges that terminate the loop on a specific tool call, not just "when LLM stops"
- **Debuggability:** state transitions visible in code
- **Recovery hook:** a `_recover_tool_call_from_text` step between the LLM output and ToolNode execution

```python
graph = StateGraph(MessagesState)
graph.add_node("agent", call_agent)      # LLM decision node
graph.add_node("tools", ToolNode(tools)) # tool execution node
graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
graph.add_conditional_edges("tools", route_after_tools, {"agent": "agent", END: END})
```

### 2.2 FPT AI Factory and Tool Call Recovery

The FPT AI Factory (OpenAI-compatible API) frequently returns tool calls as plain text instead of structured `tool_calls` in the response. Both agents carry a fallback:

```python
def _recover_tool_call_from_text(response, tools):
    # Format 1: raw JSON dict  {"user_inputs": [...]}
    # Format 2: Python call    resolve_ingredient_names(user_inputs=[...])
    # Uses ast.parse() for Format 2 — handles both single- and double-quoted dicts
```

The consumer graph uses `ast.parse` / `ast.literal_eval` to parse kwargs reliably for complex nested args like `find_recipes_for_consumer(available_ingredients=[{...}, ...], ...)`.

An `FPTChatOpenAI` adapter in `app/integrations/llm.py` also injects the `name` field into tool response messages, which FPT AI requires but LangChain doesn't add by default.

### 2.3 Tool Factory

`app/agent/shared/tool_factory.py::make_tool()` wraps any Python function as a LangChain `@tool` with JSON serialization and error handling:

```python
find_recipes_for_consumer = make_tool(
    _find,
    description="Find and score recipes for a consumer ..."
)
```

All tools return JSON strings so the LLM can reason over structured results.

---

## 3. B2B Agent

**File:** `app/agent/b2b/graph.py`

### 3.1 Flow

```text
START
  └─ agent: LLM sees system prompt + urgent inventory context
      └─ calls search_recipes_from_ingredients(ingredient_ids, urgency_dict)
          └─ agent: LLM evaluates candidates
              └─ calls check_feasibility_and_substitute(recipe, store_id) × N
                  └─ agent: LLM selects feasible recipes
                      └─ calls finalize_bundles(recipe_ids, store_id)
                          └─ route_after_tools: "finalize_bundles" in last call → END
```

The agent loop terminates as soon as `finalize_bundles` appears in the last tool call. This prevents the LLM from calling it repeatedly.

**Urgency context injection:**

Before invoking the LLM, `run_b2b_agent()` fetches urgent inventory and injects it into the system prompt:

```text
These ingredients are most at risk (sorted by urgency):
- thit_vit: score=0.92 (CRITICAL), 3 days left, 4.5kg available
- ca_ot: score=0.68 (HIGH), 7 days left, 2.0kg available
...
```

### 3.2 Tools

**`search_recipes_from_ingredients(ingredient_ids, ingredient_urgency, top_k=10)`**

Finds recipes from `DataRepository.get().recipes()` that use at least one urgent ingredient. Scores each:

```text
score = max(urgency_scores_in_recipe) + 0.3 × Σ(other urgencies)
```

Returns top-k sorted by score.

**`check_feasibility_and_substitute(recipe, store_id, inventory=None)`**

For each ingredient in the recipe:

1. Run `allocate_fefo(batches_for_ingredient, required_g, strategy="best")`
2. If allocation fails: look up substitutes from ontology, try each
3. If all fail and ingredient is optional: mark "skip"

Returns `completeness_score`, per-ingredient status, batch allocation details.

**`query_ontology(ingredient_id, relation="substitute")`**

Returns substitute ingredient IDs from `substitute_groups.json`.

**`finalize_bundles(recipe_ids, store_id, top_k=10)`**

Bridge from agent to deterministic pipeline. Given recipe IDs selected by the LLM:

1. Fetch full inventory and P1 urgency scores for `store_id`
2. For each recipe: run P3 (FEFO allocation), P5 (waste scoring)
3. Run P6 (multi-objective ranking) on all recipes together
4. Run P7 (pricing) on top-k ranked recipes
5. Return `List[BundleOutput]` as JSON

The agent controls recipe selection; the pipeline enforces pricing and margins.

### 3.3 Fallback Chain

```text
GET /api/admin/combos
  ├─ try: run_b2b_agent(store_id) → BundleOutput list
  └─ except: run_pipeline(store_id) → BundleOutput list (deterministic P1→P7)
```

---

## 4. Consumer Agent

**File:** `app/agent/consumer/graph.py`

### 4.1 Flow

Custom `StateGraph` with `MemorySaver` checkpointer for multi-turn state:

```python
memory = MemorySaver()
# keyed by thread_id — persists [HumanMessage, AIMessage, ToolMessage, ...]
config = {"configurable": {"thread_id": thread_id}}
response = await agent.ainvoke({"messages": [HumanMessage(content)]}, config=config)
```

Loop exits when the LLM produces a message without tool calls (pure text response).

### 4.2 Two Modes

**Discovery Mode** — user lists available ingredients:

```text
1. resolve_ingredient_names(["thịt heo", "trứng gà", "hành tây"])
   → [thit_heo, trung_ga, hanh_tay]
2. find_recipes_for_consumer(
     available_ingredients=[{ingredient_id, quantity_g=500, expiry_days=99}, ...],
     urgent_ingredients=[],
     allergies=[...],   ← from note_allergy results
     top_k=3
   )
   → scored recipe list
3. Agent responds; API returns recipe_suggestions array
4. User picks dish → get_remaining_ingredients(recipe_id, available_ids)
   → shopping_list in response
```

**Shopping Mode** — user names a specific dish:

```text
1. get_recipe_by_name("phở bò") → recipe dict (fuzzy match)
2. resolve_ingredient_names([user's available items])
3. get_remaining_ingredients(recipe_id, available_ingredient_ids)
   → {to_buy: [{ingredient_id, name, required_qty_g, estimated_unit_price, ...}]}
4. API returns shopping_list; ShoppingListPanel renders with per-item checkboxes
```

### 4.3 Allergy Handling

`note_allergy` is a "tool-as-memory" pattern. When the user mentions an allergy:

1. Agent calls `note_allergy(allergy_names=["tôm"])` immediately
2. Tool resolves name → ingredient ID, returns `{"allergy_ids": ["tom"], ...}`
3. This creates a `ToolMessage` persisted in conversation history by `MemorySaver`
4. On subsequent turns, the LLM reads prior `note_allergy` results and passes IDs to `find_recipes_for_consumer(allergies=[...])`

This is more reliable than instructing the LLM to "remember allergies" — the structured tool result is always in the message history.

### 4.4 API Response Shape

`POST /consumer/chat` returns:

```json
{
  "reply": "...",
  "thread_id": "...",
  "shopping_list": [
    {
      "ingredient_id": "hanh_tay",
      "name": "hành tây",
      "required_qty_g": 150,
      "estimated_unit_price": 8000,
      "sku_id": "SKU-V002",
      "is_optional": false
    }
  ],
  "recipe_suggestions": [
    {
      "recipe_id": "R003",
      "name": "Thịt heo xay chưng trứng",
      "score": 2.0,
      "ingredients": [
        {"name": "trứng gà", "have": true, "optional": false},
        {"name": "thịt heo xay", "have": false, "optional": false},
        {"name": "hành lá", "have": false, "optional": true}
      ]
    }
  ]
}
```

`recipe_suggestions` is extracted from the last `find_recipes_for_consumer` ToolMessage in the conversation history by `_extract_recipe_suggestions()` in `graph.py`. The `have` flag is set by comparing each recipe ingredient ID against the resolved IDs the user provided.

### 4.5 Price Accuracy

Shopping list prices come from `DataRepository.ingredient_sku_lookup()`, keyed by `ingredient_id`. (An earlier version used `sku_dict_lookup()` keyed by `sku_id`, which always missed and returned price=0.)

---

## 5. Deterministic Pipeline (P1–P7)

**Orchestrator:** `app/core/pipeline/orchestrator.py`

Chain of Responsibility pattern — each `PipelineStage` reads from `PipelineContext`, writes results back, passes context to next stage.

### 5.1 P1 — Priority Scoring

Scores each batch by urgency. Three components:

```python
# Expiry decay — exponential, rate λ varies by category
expiry_score = exp(-λ × expiry_days)

# Supply/demand ratio — sigmoid
days_of_supply = remaining_qty_g / avg_daily_sales
supply_score = sigmoid(days_of_supply / max(expiry_days, 1) - 1)

# Demand weakness — inverse sell-through
sell_through = total_sold / (total_sold + remaining_qty_g)
demand_score = 1 - sell_through

priority = w_e × expiry_score + w_s × supply_score + w_d × demand_score
```

**Category parameters:**

| Category | λ | w_e | w_s | w_d |
| --- | --- | --- | --- | --- |
| fresh_seafood | 0.60 | 0.65 | 0.25 | 0.10 |
| fresh_meat | 0.50 | 0.65 | 0.25 | 0.10 |
| fresh_produce | 0.25 | 0.55 | 0.30 | 0.15 |
| dairy | 0.12 | 0.45 | 0.35 | 0.20 |
| processed | 0.08 | 0.30 | 0.45 | 0.25 |

Assigns `urgency_flag`: CRITICAL (≥0.80), HIGH (≥0.65), MEDIUM (≥0.40), WATCH (<0.40).

Output cached in `p1_cache` for `/api/admin/inventory` queries.

### 5.2 P2 — Recipe Retrieval

Groups P1 batches by `ingredient_id`, then for each recipe:

```text
score = max(priority_scores of matched ingredients)
      + 0.3 × Σ(other matched ingredient priorities)
```

Returns top-k recipes by `urgency_coverage_score`.

### 5.3 P3 — Feasibility

For each recipe ingredient:

1. `allocate_fefo(batches, required_g, strategy="best")`
2. If fails: try substitutes from ontology in order
3. If all fail and optional: mark "skip"

`completeness_score = (n_required_fulfilled + 0.3 × n_optional_fulfilled) / n_total`

Recipes with completeness < 0.70 are discarded.

### 5.4 P5 — Waste Scoring

```text
waste_score = Σ (priority_score × cost_per_gram × qty_taken_g)
              for CRITICAL and HIGH ingredients only
waste_score_normalized = waste_score / max(waste_score across recipes)
```

### 5.5 P6 — Multi-Objective Ranking

```text
final_score = w1 × urgency_coverage
            + w2 × completeness
            + w3 × waste_norm
            − w4 × avg_deviation
            − w5 × norm_rounding_loss
            + w_popularity × popularity
            − substitute_penalty
```

**Cold-start weights** (no popularity data): w1=0.50, w2=0.30, w3=0.20, rest=0.

Weights stored in Firestore per store; defaults from `default_weights.json`.

### 5.6 P7 — Dynamic Pricing

```python
raw_discount = min(0.05 + 0.25 × waste_norm, 0.30)   # 5–30% range
final_price = bundle_retail × (1 - raw_discount)

# Margin floor check
weighted_margin = Σ(ingredient_cost × category_min_margin) / Σ(ingredient_cost)
if (final_price - bundle_cost) / final_price < weighted_margin:
    final_price = bundle_cost / (1 - weighted_margin)
```

Outputs `List[BundleOutput]` with `original_price`, `discount_rate`, `final_price`, `gross_margin`, per-ingredient allocation details.

---

## 6. FEFO Allocation Engine

**File:** `app/core/engine/allocation.py::allocate_fefo()`

Allocates discrete packets (not continuous grams) respecting FEFO order.

```python
def allocate_fefo(batches, required_g, strategy="best"):
    # Batches sorted by expiry_days ascending
    # For each batch: take ceil or floor of (remaining_needed / pack_size) packets
    # Stop when remaining_needed <= 0
```

**Three strategies:**

| Strategy | Rounding | When to use |
| --- | --- | --- |
| `strict` | `ceil()` | Must meet recipe requirements exactly |
| `approx` | `floor()` | Minimize waste; may under-deliver slightly |
| `best` | strict first, fallback to approx | Default; picks lower deviation |

**`best` logic:** run strict, check `deviation = |allocated - required| / required`. If feasible (≤ 25% deviation), use strict. Else try approx, pick whichever has lower deviation.

---

## 7. Ingredient Ontology

**File:** `app/core/data/substitute_groups.json`

29 Vietnamese cuisine substitution groups. Examples:

```json
{
  "thit_heo": ["thit_ga", "thit_bo", "thit_de"],
  "tom":       ["muc", "ngheu", "so_huyet"],
  "hanh_tay":  ["hanh_ta_trang", "hanh_tia"],
  "nuoc_mam":  ["nuoc_cot"]
}
```

**Used by:**

- **P3:** if primary ingredient unavailable, try substitutes in order
- **B2B agent:** `query_ontology` tool exposes this to LLM reasoning
- **Consumer agent:** allergy filtering — if allergen has no safe substitute available, exclude recipe; `get_ingredient_suggestions` returns alternatives for missing shopping items

---

## 8. Data Layer

**File:** `app/core/data/repository.py`

`DataRepository` is a singleton with `@lru_cache` on all methods:

```python
class DataRepository:
    _instance = None

    @classmethod
    def get(cls) -> "DataRepository":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @lru_cache(maxsize=1)
    def recipes(self) -> List[dict]: ...

    @lru_cache(maxsize=1)
    def skus(self) -> List[dict]: ...

    @lru_cache(maxsize=1)
    def ingredient_aliases(self) -> Dict[str, str]: ...  # alias → ingredient_id

    @lru_cache(maxsize=1)
    def ingredient_sku_lookup(self) -> Dict[str, dict]: ...  # ingredient_id → SKU dict
```

**All agent tools read from `DataRepository`** — no tool reads from test fixtures or raw JSON files directly. This ensures a single canonical source of truth.

**`ingredient_aliases.json`** is organized by category (proteins, vegetables, sauces_pantry, etc.) and flattened by the repository. 178 aliases map Vietnamese free-text names (with and without tone marks) to canonical ingredient IDs.

---

## 9. Frontend Integration

**Stack:** Next.js App Router, all pages as `"use client"` components.

### 9.1 Pages

| Route | Component | Purpose |
| --- | --- | --- |
| `/` | `page.js` | Portal selector (Admin / Customer) |
| `/admin` | `admin/page.js` | Bundle suggestions + at-risk inventory |
| `/customer` | `customer/page.js` | Combo browser for purchase |
| `/customer/ai-chat` | `ai-chat/page.js` | Consumer agent chat |
| `/customer/cart` | `cart/page.js` | Shopping cart (localStorage) |

### 9.2 Admin Portal

Loads combos and inventory in parallel on mount:

```javascript
Promise.allSettled([
    fetchAdminCombos({ storeId, limit }),
    fetchAdminInventory({ storeId, daysThreshold }),
])
```

Combo cards show: name, discount %, confidence score, ingredient list, urgency badges. Clicking a card opens `ComboDetailModal`. Accept/Reject buttons POST to backend (currently logged, not persisted).

### 9.3 AI Chat

**State:**

```javascript
messages:          [{id, type: "bot"|"user", text, shoppingList?, recipeSuggestions?}]
threadId:          persisted in useRef across renders
allergies:         chip list in footer (user-entered tags sent with each message)
allergyInput:      text input for adding new allergy chips
```

**`RecipeSuggestionCard`** — expand/collapse component:

- Collapsed: shows recipe name + chevron
- Expanded: lists all ingredients with green dot (user has it) or gray dot + "cần mua" (user needs it)

**`ShoppingListPanel`** — per-item checkboxes:

- All items pre-selected
- `useEffect` deselects items matching any allergy chip
- "Thêm N nguyên liệu vào giỏ hàng" adds selected items to `localStorage` cart

### 9.4 API Clients

`lib/adminApi.js` and `lib/customerApi.js` share a `requestJson(path, opts)` base function. All responses are mapped from backend snake_case to frontend camelCase before entering component state.

```javascript
export async function sendConsumerChat({ message, threadId, allergies }) {
    const payload = await requestJson("/consumer/chat", {
        method: "POST",
        body: { message, thread_id: threadId, ...(allergies?.length ? { allergies } : {}) },
    });
    return {
        reply: payload.reply,
        threadId: payload.thread_id,
        shoppingList: payload.shopping_list ?? null,
        recipeSuggestions: payload.recipe_suggestions ?? null,
    };
}
```

---

## 10. Testing

**85 passing, 14 failing** as of April 2026.

| File | Covers |
| --- | --- |
| `test_allocation.py` | FEFO strategies, deviation bounds, packet math |
| `test_p1_priority.py` | Urgency scoring by category, flag thresholds |
| `test_p2_retrieval.py` | Recipe candidate scoring |
| `test_p3_feasibility.py` | Allocation + substitution + completeness |
| `test_p5_waste.py` | Waste score composition and normalization |
| `test_p6_ranking.py` | Weighted scoring, rank ordering |
| `test_p7_pricing.py` | Discount bounds, margin floor enforcement |
| `test_pipeline_integration.py` | Full P1→P7 with mock data |
| `test_b2b_agent.py` | B2B tool logic (feasibility, search) |
| `test_consumer_agent.py` | Consumer tool logic |
| `test_agent_integration.py` | Cross-agent integration |

All tests use deterministic fixture data from `tests/fixtures/`. No external API calls required.

**Known failures:**

- 5 tests in `test_b2b_agent.py::TestCheckFeasibilityWithPacketAllocation` — packet metrics assertions
- `test_p6_ranking.py::test_run_p6_ranks` — index error in ranking output
- `test_pipeline_integration.py::test_full_pipeline` — zero bundles returned

---

## 11. Deployment

### 11.1 Environment Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | For agents | FPT AI Factory key |
| `OPENAI_MODEL` | No (default: `gpt-oss-120b`) | LLM model ID |
| `TEMPERATURE` | No (default: `0.1`) | Sampling temperature |
| `DEFAULT_CONNECTOR` | No (default: `mock`) | `mock` or `postgres` |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend base URL |

### 11.2 Docker

```bash
docker-compose up --build
# backend:  http://localhost:8000   (Swagger: /docs)
# frontend: http://localhost:3000
```

### 11.3 Scaling Notes

| Component | Current | Production path |
| --- | --- | --- |
| Bundle cache | Process-local dict (6h TTL) | Redis with multi-worker support |
| Consumer chat state | `MemorySaver` (in-memory) | `AsyncPostgresSaver` |
| DataRepository | Process-local singleton (read-only) | No change needed |
| P1 cache | Process-local dict | Redis (key: store_id) |
| LLM calls | Synchronous in LangGraph | Keep `recursion_limit` ≤ 80 |
