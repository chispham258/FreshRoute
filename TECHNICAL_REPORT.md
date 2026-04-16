# FreshRoute — Technical Report

**Project:** FreshRoute — AI-Powered Food Waste Reduction for Vietnamese Retailers  
**Stack:** Python 3.13 · FastAPI · LangGraph · FPT AI Factory · Next.js 16 · Pydantic v2  
**Date:** April 2026

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Solution Overview](#2-solution-overview)
3. [System Architecture](#3-system-architecture)
4. [P1–P7 Pipeline Specification](#4-p1p7-pipeline-specification)
5. [FEFO Allocation Engine](#5-fefo-allocation-engine)
6. [Agent Layer](#6-agent-layer)
7. [Ingredient Ontology](#7-ingredient-ontology)
8. [Frontend Architecture](#8-frontend-architecture)
9. [API Design](#9-api-design)
10. [Data Models](#10-data-models)
11. [Data Flow](#11-data-flow)
12. [Reference Data](#12-reference-data)
13. [Testing Strategy](#13-testing-strategy)
14. [Deployment](#14-deployment)

---

## 1. Problem Statement

Food waste in Vietnamese retail is concentrated in the last 2–3 days before a product expires. At that point:

- Supermarkets have priced items at full retail, making them unattractive vs. fresher stock
- Bundle promotions are created manually, too slowly and inconsistently
- Home consumers do not know which of their own ingredients are about to expire or how to use them together

The cost is substantial: unsold perishables are discarded at full cost price, and the environmental impact compounds through cold chain energy waste.

FreshRoute addresses both sides: it helps stores create data-driven bundle deals from near-expiry inventory at the right discount, and it helps home cooks plan meals around what they already have before it goes bad.

---

## 2. Solution Overview

FreshRoute has two tightly coupled features sharing the same data layer and ingredient ontology.

### Feature 1 — B2B Store Bundle Engine

A deterministic seven-stage pipeline (P1–P7) that ingests a store's current inventory, identifies batches at highest risk of expiry, matches them to Vietnamese recipes, checks whether the store can fulfil each recipe from current stock, and outputs ranked, margin-safe, discounted bundle recommendations. An optional LangGraph agent runs the same logic through an LLM for richer reasoning.

### Feature 2 — Consumer Cooking Assistant

A multi-turn conversational agent (Vietnamese language) that operates in two modes: Discovery Mode (user has ingredients, agent suggests recipes prioritising near-expiry items) and Shopping Mode (user names a dish, agent computes a shopping list from what they already have).

Both features are surfaced through a fullstack application: a Next.js 16 frontend with dedicated admin and customer portals backed by a FastAPI server.

---

## 3. System Architecture

### 3.1 Layer Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js 16)                  │
│   /admin  ·  /customer  ·  /customer/ai-chat               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (fetch via api.js)
┌────────────────────────▼────────────────────────────────────┐
│                       API Layer (FastAPI)                    │
│  /bundles  ·  /api/admin  ·  /consumer  ·  /metrics        │
└───────────┬────────────────────────┬────────────────────────┘
            │                        │
┌───────────▼──────────┐  ┌──────────▼──────────────┐
│  Deterministic        │  │   Agent Layer            │
│  Pipeline (P1–P7)     │  │   B2B Agent (StateGraph) │
│  Chain of             │  │   Consumer Agent         │
│  Responsibility       │  │   (create_react_agent)   │
└───────────┬──────────┘  └──────────┬───────────────┘
            └──────────────┬──────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Core Domain Layer                       │
│  DataRepository · AllocationEngine · Pydantic Models        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Integrations Layer                        │
│  FPTChatOpenAI · MockConnector · Firestore · PostgreSQL     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Design Patterns

| Pattern | Location | Purpose |
| --- | --- | --- |
| Singleton | `DataRepository` | One source of truth for static reference data |
| Chain of Responsibility | `PipelineStage`, `PipelineChain` | P1–P7 stages sharing an immutable context |
| Factory | `make_tool()`, `get_llm()` | Wrap functions as LangChain tools; create LLM instances |
| Strategy | `allocate_fefo(strategy=...)` | `strict` / `approx` / `best` allocation behaviours |
| Facade | `run_pipeline()` | Single entry point over the seven-stage pipeline |
| Adapter | `StoreConnector` ABC | Decouple data source from domain logic |
| State Machine | LangGraph `StateGraph` | Typed agent state with conditional routing edges |

### 3.3 Directory Structure

```text
app/
├── core/                    Framework-free domain logic
│   ├── pipeline/            P1–P7 stages + orchestrator
│   ├── engine/              Packet-based FEFO allocation
│   ├── data/                DataRepository, SKUs, recipes, JSON configs
│   └── models/              Pydantic schemas
├── agent/
│   ├── shared/              tool_factory.py, ontology.py
│   ├── b2b/                 B2B agent (graph, tools, prompt)
│   ├── consumer/            Consumer agent (graph, tools, prompt, state)
│   └── tools.py             Core tool implementations
├── api/                     FastAPI route handlers
├── integrations/            LLM wrapper, connectors, DB clients
├── config.py                Pydantic BaseSettings
├── dependencies.py          FastAPI DI
└── main.py                  Entry point

frontend/
└── src/
    ├── app/admin/           Admin portal
    ├── app/customer/        Customer + AI chat portals
    ├── components/admin/    AnalyticsDashboard, ComboDetailModal
    └── lib/api.js           Centralised API client
```

---

## 4. P1–P7 Pipeline Specification

The pipeline runs as a `PipelineChain`. Each `PipelineStage` receives the shared `PipelineContext`, enriches it, and passes it on. Stage exceptions are caught without halting the chain.

```python
bundles = await run_pipeline(
    store_id="BHX-HCM001",
    connector=MockConnector(),
    top_n=20,     # P1 batch count
    top_k_p2=20,  # P2 recipe candidates
    top_k_p6=10,  # P6 final bundle count
)
```

### 4.1 P1 — Inventory Risk Scoring

**Input:** All store batches + 14-day sales history per SKU  
**Output:** `List[P1Output]` sorted by priority score

**Scoring formula:**

```text
priority_score = w_e × expiry_score + w_s × supply_score + w_d × demand_score

expiry_score  = exp(−λ × expiry_days)                              # exponential decay
supply_score  = sigmoid(days_of_supply / max(expiry_days, 1) − 1)  # supply/demand ratio
demand_score  = 1 − total_sold / (total_sold + remaining_qty_g)    # sell-through inversion
```

**Category parameters:**

| Category | λ | w_e | w_s | w_d |
| --- | --- | --- | --- | --- |
| fresh_seafood | 0.60 | 0.65 | 0.25 | 0.10 |
| fresh_meat | 0.50 | 0.65 | 0.25 | 0.10 |
| fresh_produce | 0.25 | 0.55 | 0.30 | 0.15 |
| dairy | 0.12 | 0.45 | 0.35 | 0.20 |
| processed | 0.08 | 0.30 | 0.45 | 0.25 |

**Urgency thresholds:**

| Flag | Score | Strategy |
| --- | --- | --- |
| `CRITICAL` | ≥ 0.80 | Move at any discount |
| `HIGH` | ≥ 0.65 | Aggressive discount |
| `MEDIUM` | ≥ 0.50 | Standard discount |
| `WATCH` | < 0.50 | Monitor only |

### 4.2 P2 — Recipe Retrieval

**Input:** P1 batches + inverted index (`ingredient_id → [recipe_ids]`)  
**Output:** Top-K recipe candidates scored by urgency coverage

```text
urgency_coverage = max_priority_in_recipe + 0.3 × sum(other_matched_priorities)
```

Recipes are filtered to those matching at least one urgent ingredient, then sorted by coverage score and truncated to `top_k_p2`. This formula ensures recipes using the single most-critical ingredient rank above recipes matching many low-urgency ingredients.

### 4.3 P3 — Feasibility Check

**Input:** P2 candidates + full inventory + substitute groups  
**Output:** Per-ingredient status + `completeness_score`

For each recipe ingredient:

1. Find matching batches (by `ingredient_id`)
2. Run `allocate_fefo()` on those batches
3. If infeasible, try each substitute from the ontology
4. Assign status: `fulfilled` | `substitute` | `skip` (optional) | `missing` (required)

```text
completeness = (required_fulfilled + 0.3 × optional_fulfilled)
             / (required_total + 0.3 × optional_total)
```

Recipes with `completeness < 0.7` are discarded. The `ingredient_status[]` list records `batches_used` per ingredient, which P7 uses for accurate pricing.

### 4.4 P5 — Waste Value Scoring

**Input:** P3 feasible recipes + SKU costs  
**Output:** `waste_score` and `waste_score_normalized`

```text
waste_score = Σ (priority_score × cost_per_gram × qty_taken_g)
              for each ingredient where urgency ∈ {CRITICAL, HIGH} and status == "fulfilled"

waste_score_normalized = (score − min) / (max − min)   # across all candidates
```

### 4.5 P6 — Multi-Objective Ranking

**Input:** P5 recipes + weights (Firestore or `default_weights.json`)  
**Output:** Top-K recipes with `rank` and `final_score`

```text
final_score = w1 × urgency_coverage_score
            + w2 × completeness_score
            + w3 × waste_score_normalized
            − w4 × avg_deviation
            − w5 × total_rounding_loss_g / 1000
            + w_popularity × popularity_score
            − substitute_penalty

substitute_penalty = 0.05 × (n_substitute / n_total_ingredients)
```

**Default weights (cold start — no popularity data):**

| Weight | Value | Factor |
| --- | --- | --- |
| w1 (urgency) | 0.50 | Urgency coverage |
| w2 (completeness) | 0.30 | Feasibility |
| w3 (waste) | 0.20 | Waste value rescued |
| w4 (deviation) | 0.00 | Disabled at cold start |
| w_popularity | 0.00 | Disabled at cold start |

Switches to `with_popularity` weights once impression data accumulates.

### 4.6 P7 — Dynamic Pricing

**Input:** P6 ranked recipes + SKU retail/cost prices + category margins  
**Output:** `List[BundleOutput]` with full pricing

```text
bundle_retail = Σ (retail_price_per_gram × qty_taken_g)  for each batch used
bundle_cost   = Σ (cost_price_per_gram  × qty_taken_g)

raw_discount      = min(0.05 + 0.25 × waste_score_normalized, 0.30)
discounted_price  = bundle_retail × (1 − raw_discount)

# Margin floor check
achieved_margin = (discounted_price − bundle_cost) / discounted_price
if achieved_margin >= min_margin:
    final_price = discounted_price
else:
    final_price = bundle_cost / (1 − min_margin)   # floor to protect margin

# Weighted minimum margin by category cost proportion
min_margin = Σ (category_margin[cat] × cat_cost / bundle_cost)
```

**Category minimum margins:**

| Category | Min Margin |
| --- | --- |
| fresh_meat | 12% |
| fresh_seafood | 15% |
| dairy | 18% |
| fresh_produce | 20% |
| processed | 25% |

Discount is bounded between 5% (minimum deal) and 30% (maximum allowed discount). Every bundle ingredient is enriched with its `urgency_flag` from the P1 lookup.

---

## 5. FEFO Allocation Engine

**File:** `app/core/engine/allocation.py`

Allocates discrete inventory packets (not continuous grams) respecting First-Expiry-First-Out ordering.

### 5.1 Result Structure

```python
@dataclass
class AllocationResult:
    packets_used: int
    allocated_g: float
    deviation: float          # |allocated − required| / required
    strategy: Literal["strict", "approx"]
    batches_used: List[dict]  # [{batch_id, sku_id, packets_taken, grams_taken}]
    feasible: bool
```

### 5.2 Strategies

| Strategy | Rounding | Behaviour |
| --- | --- | --- |
| `strict` | `ceil()` packs | May slightly over-allocate; ensures required grams are met |
| `approx` | `floor()` packs | May under-allocate; avoids wasting a full extra pack |
| `best` | Tries `strict` first | Falls back to `approx` if deviation > 25% |

```python
def allocate_fefo(batches, required_g, strategy="best"):
    # Sort batches by expiry_days ASC (earliest first — FEFO)
    for batch in sorted_batches:
        packets_to_take = ceil_or_floor(remaining_needed / pack_size_g)
        packets_to_take = min(packets_to_take, batch.unit_count)
        grams_taken = packets_to_take × pack_size_g
        # accumulate...

    deviation = |allocated_g − required_g| / required_g
    feasible = (allocated_g >= required_g)
```

`MAX_DEVIATION = 0.25` — allocations exceeding 25% deviation are penalised in P6 ranking.

---

## 6. Agent Layer

### 6.1 B2B Store Bundle Agent

**File:** `app/agent/b2b/graph.py`

Uses a custom `StateGraph` (not `create_react_agent`) with a conditional edge that terminates the loop immediately after `finalize_bundles` completes, preventing repeated calls.

```text
START
  │
  ▼
[agent] ──(tool calls?)──► [tools] ──(finalize_bundles?)──► END
  ▲                            │
  └────────(other tools)───────┘
```

**Workflow:**

1. Pre-compute P1 urgent inventory deterministically (no LLM)
2. Build `ingredient_urgency` dict (`ingredient_id → priority_score`) and inject into prompt
3. LLM calls `search_recipes_from_ingredients` with urgent IDs + urgency weights
4. LLM calls `check_feasibility_and_substitute` for each candidate
5. LLM calls `query_ontology` when substitutes are needed
6. When 3–10 feasible recipes are collected, LLM calls `finalize_bundles` once
7. `finalize_bundles` runs P5 → P6 → P7 and returns `List[BundleOutput]`

**FPT model fallback:** The FPT AI model occasionally returns tool arguments as JSON text rather than structured `tool_calls`. The agent detects this by checking whether `response.content` is a JSON dict whose required keys match a registered tool's schema, then reconstructs a proper `AIMessage` with `tool_calls`.

**B2B tools:**

| Tool | Input | Output |
| --- | --- | --- |
| `search_recipes_from_ingredients` | `ingredient_ids`, `ingredient_urgency` | Recipes sorted by P2 urgency-weighted score |
| `check_feasibility_and_substitute` | `recipe`, `full_inventory` | Feasibility result with `ingredient_status[]` |
| `query_ontology` | `ingredient_id`, `relation` | Substitute IDs from ontology |
| `finalize_bundles` | `recipe_ids[]`, `store_id`, `top_k` | Priced `BundleOutput` JSON |

**Urgency-weighted recipe search:** `search_recipes_from_ingredients` accepts an optional `ingredient_urgency` dict. When provided, it applies the same P2 formula (`max_priority + 0.3 × sum(others)`) rather than a simple match count, ensuring the agent ranks recipes the same way the deterministic pipeline does.

### 6.2 Consumer Home Cooking Agent

**File:** `app/agent/consumer/graph.py`

Uses `create_react_agent` with `MemorySaver` checkpointer for persistent multi-turn state keyed by `thread_id`.

**Discovery Mode** (user has ingredients, doesn't know what to cook):

```text
resolve_ingredient_names → get_user_urgent_ingredients
  → find_recipes_for_consumer → (adjust_recipe_for_user if allergies)
```

**Shopping Mode** (user knows the dish, needs a shopping list):

```text
get_recipe_by_name → get_remaining_ingredients → get_ingredient_suggestions
```

**Consumer tools:**

| Tool | Description |
| --- | --- |
| `resolve_ingredient_names` | Map Vietnamese free-text → `ingredient_id` via aliases |
| `get_user_urgent_ingredients` | Filter user inventory to near-expiry items |
| `find_recipes_for_consumer` | Score recipes by urgency + allergy compatibility |
| `adjust_recipe_for_user` | Substitute allergens and unavailable ingredients |
| `get_recipe_by_name` | Fuzzy-match Vietnamese recipe name |
| `get_remaining_ingredients` | Compute shopping list from what user already has |
| `get_ingredient_suggestions` | Ontology-based alternatives for missing ingredients |
| `query_ontology` | Direct ontology lookup |

### 6.3 Tool Factory

**File:** `app/agent/shared/tool_factory.py`

```python
def make_tool(fn, serialize_output=True, name=None, description=None):
    @tool
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        return json.dumps(result, ensure_ascii=False, default=str) if serialize_output else result
    return wrapper
```

All tool errors are returned as `{"error": "...", "type": "..."}` so the LLM can recover gracefully rather than the agent graph crashing.

### 6.4 LLM Integration

**File:** `app/integrations/llm.py`

`FPTChatOpenAI` extends `langchain_openai.ChatOpenAI` with a `_get_request_payload` override that fixes FPT AI Factory's tool response format requirements:

- Builds a `tool_call_id → tool_name` mapping from assistant messages
- Injects the `name` field into every tool response (FPT AI requires it; OpenAI spec makes it optional)
- Serialises `content` to string (FPT AI rejects structured content objects)

`get_llm()` is not cached, so `OPENAI_MODEL` env var changes take effect immediately without restart.

---

## 7. Ingredient Ontology

**Files:** `app/core/data/substitute_groups.json`, `app/agent/shared/ontology.py`

29 substitution groups covering Vietnamese cuisine:

```json
{
  "thit_heo": ["thit_ga", "thit_bo", "thit_de"],
  "ca_loc":   ["ca_ro", "ca_tram", "ca_chep"],
  "tom":      ["muc", "ngheu", "so_huyet"]
}
```

**API:**

```python
query_ontology("thit_heo", relation="substitute")
# → {"ingredient_id": "thit_heo", "relation": "substitute", "substitutes": ["thit_ga", "thit_bo", ...]}

are_substitutes("thit_heo", "thit_ga")  # → True (bidirectional)
```

**Uses across the system:**

1. **P3 Feasibility** — when primary ingredient is out of stock, try each substitute in order
2. **B2B agent** — `query_ontology` tool called when LLM needs alternatives for missing items
3. **Consumer agent** — allergy filter blocks substitutes that match the user's allergy list
4. **Shopping mode** — `get_ingredient_suggestions` uses ontology to propose what to buy instead

**Ingredient aliases** (`ingredient_aliases.json`) map Vietnamese free-text variations to canonical IDs:

```json
{
  "thịt heo": "thit_heo",
  "thịt lợn": "thit_heo",
  "cà chua":  "ca_chua",
  "tomato":   "ca_chua"
}
```

Used by `resolve_ingredient_names` and `DataRepository.ingredient_aliases()`.

---

## 8. Frontend Architecture

### 8.1 Technology

- **Next.js 16.2.3** with App Router, all pages as client components (`"use client"`)
- **React 19.2.4** with hooks for state and side effects
- **Tailwind CSS 4** for styling
- **Framer Motion** for UI animations
- **Centralised API client** (`src/lib/api.js`) using `fetch` with a generic error-handling wrapper

### 8.2 API Client

```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI(endpoint, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
```

All pages import named functions from `api.js` rather than calling `fetch` directly.

### 8.3 Admin Portal (`/admin`)

Connects to three backend endpoints on mount:

| Backend Endpoint | Data |
| --- | --- |
| `GET /api/admin/combos?storeId=BHX-HCM001` | AI-suggested combo cards |
| `GET /api/admin/inventory?storeId=BHX-HCM001` | Near-expiry inventory list |
| `GET /metrics/BHX-HCM001` | Revenue and sales KPIs |

**Data adaptations applied in the frontend:**

- `combo.aiReasoning` (backend) → `combo.aiReason` (frontend field name)
- `combo.ingredients[{name, quantity, unit}]` → `"Thịt heo 500g"` display strings
- `inventory.weight` (grams float) → `"X.X kg"` display string
- `metrics.total_revenue` (VNĐ) → `totalRevenue` in millions

Accept and reject actions call `POST /api/admin/combos/{id}/accept|reject` with `{ storeId, reason }`.

### 8.4 Customer Portal (`/customer`)

Fetches `GET /consumer/api/customer/combos?storeId=BHX-HCM001` on mount.

**Data adaptations:**

- `image: null` → fallback Unsplash image
- `tags: null` → `[]`
- `ingredient.status: "Sắp hết"` → `"warning"` (matches CSS status class)
- `ingredient.status: "Bình thường"` → `"safe"`

### 8.5 AI Chat Portal (`/customer/ai-chat`)

A stateful multi-turn chat UI. Each session generates a random `thread_id` on mount. Messages are sent to `POST /consumer/chat` with the current `thread_id`, and the text `reply` from the response is rendered as a bot message.

The `TypingIndicator` component animates while waiting for the API response. On error, a Vietnamese-language fallback message is shown.

### 8.6 Shopping Cart (`/customer/cart`)

Cart is local state only — no backend cart API exists. Items are added from the customer combo page and are not persisted across page navigations in the current implementation.

---

## 9. API Design

### 9.1 Bundle Endpoints (`api/bundles.py`)

**In-memory cache with stale-while-revalidate:**

```text
Request
  │
  ▼
Cache hit and age < 6h? → serve cached bundles
  │ miss or expired
  ▼
run_pipeline() or run_b2b_agent()
  │
  ▼
Store in _bundle_cache[store_id]
  │ if 3h < age < 6h on a cache hit
  ▼
BackgroundTask: silently refresh cache
```

Cache is process-local (`dict`). For multi-worker deployments, replace with Redis.

### 9.2 Consumer Endpoints (`api/consumer.py`)

Each `POST /consumer/chat` request passes a `thread_id`. LangGraph's `MemorySaver` checkpointer stores the full conversation state keyed by `thread_id`. Follow-up messages receive the complete prior context automatically.

### 9.3 Request / Response Schemas

**ChatRequest:**

```python
class ChatRequest(BaseModel):
    message: str
    thread_id: str
    user_id: Optional[str] = None
    allergies: List[str] = []
    dietary_preferences: List[str] = []
```

**SuggestRequest / SuggestResponse:**

```python
class SuggestRequest(BaseModel):
    ingredients: List[str]   # Vietnamese free-text or ingredient IDs
    allergies: List[str] = []
    top_k: int = 5

class SuggestResponse(BaseModel):
    resolved_ingredients: List[dict]
    unresolved_ingredients: List[str]
    allergy_ids: List[str]
    suggestions: List[dict]  # recipe feasibility results
```

---

## 10. Data Models

### 10.1 Inventory (`core/models/inventory.py`)

```python
class ProductSKU(BaseModel):
    sku_id: str
    ingredient_id: str
    product_name: str
    category_l1: Literal["fresh_meat", "fresh_seafood", "fresh_produce", "dairy", "processed"]
    unit_type: Literal["kg", "piece", "pack", "bottle", "bag"]
    pack_size_g: float      # grams per discrete packet
    retail_price: float     # VND per pack
    cost_price: float       # VND per pack

class ProductBatch(BaseModel):
    batch_id: str
    sku_id: str
    ingredient_id: str
    store_id: str
    unit_count: int         # discrete packets in stock
    pack_size_g: float
    expiry_date: date
    expiry_days: int
    cost_price: float

    @property
    def total_quantity_g(self) -> float:
        return self.unit_count * self.pack_size_g

class P1Output(BaseModel):
    batch_id: str
    ingredient_id: str
    priority_score: float   # 0.0 – 1.0
    expiry_days: int
    urgency_flag: Literal["CRITICAL", "HIGH", "MEDIUM", "WATCH"]
```

### 10.2 Bundle (`core/models/bundle.py`)

```python
class BundleIngredientDisplay(BaseModel):
    ingredient_id: str
    sku_id: str
    product_name: str
    qty_taken_g: float
    item_retail_price: float
    is_substitute: bool
    substitute_id: Optional[str]
    urgency_flag: Optional[str]

class BundleOutput(BaseModel):
    bundle_id: str              # "{recipe_id}__{store_id}__{date}"
    recipe_id: str
    recipe_name: str
    rank: int
    final_score: float
    urgency_coverage_score: float
    completeness_score: float
    waste_score_normalized: float
    original_price: float
    discount_rate: float        # 0.05 – 0.30
    final_price: float
    gross_profit: float
    gross_margin: float
    ingredients: List[BundleIngredientDisplay]
    has_substitute: bool
    store_id: str
    generated_at: datetime
    avg_deviation: float
    total_rounding_loss_g: float
    allocation_strategy: str    # "strict" | "approx" | "none"
```

### 10.3 Recipe (`core/models/recipe.py`)

```python
class RecipeRequirement(BaseModel):
    ingredient_id: str
    required_qty_g: float
    is_optional: bool = False
    role: str = "main"          # main | seasoning | garnish

class Recipe(BaseModel):
    recipe_id: str
    name: str                   # Vietnamese dish name
    servings: int
    category: str
    ingredients: List[RecipeRequirement]
```

### 10.4 DataRepository

**File:** `app/core/data/repository.py`

Singleton with lazy-loaded, LRU-cached derived lookups:

```python
repo = DataRepository.get()

# Primary data (loaded once)
repo.skus()               # List[dict] — all 80+ SKUs
repo.recipes()            # List[dict] — all 40+ recipes
repo.substitute_groups()  # {ingredient_id: [substitutes]}
repo.ingredient_aliases() # {vietnamese_name: ingredient_id}
repo.default_weights()    # {mode: {w1, w2, w3, ...}}
repo.category_margins()   # {category: float}

# Derived lookups (LRU cached)
repo.sku_lookup()          # {sku_id: ProductSKU}
repo.recipe_lookup()       # {recipe_id: dict}
repo.recipe_names()        # {recipe_id: name}
repo.recipe_requirements() # {recipe_id: [RecipeRequirement]}
repo.inverted_index()      # {ingredient_id: [recipe_ids]}
```

---

## 11. Data Flow

### 11.1 Deterministic Bundle Generation

```text
HTTP GET /bundles/BHX-HCM001
  │
  ▼ cache miss or force_refresh=True
run_pipeline(store_id, connector)
  ├─ connector.get_batches()         → List[ProductBatch]
  ├─ connector.get_sales_history()   → {sku_id: [sales]}
  └─ DataRepository.get()
       ├─ sku_lookup()               → {sku_id: ProductSKU}
       ├─ recipe_lookup()            → {recipe_id: Recipe}
       ├─ inverted_index()           → {ingredient_id: [recipe_ids]}
       └─ substitute_groups()        → {ingredient_id: [substitutes]}
  │
  ▼
PipelineChain.execute(context)
  ├─ P1: context.p1_output + p1_ingredient_lookup
  ├─ P2: context.p2_output (urgency-scored candidates)
  ├─ P3: context.p3_output (feasibility + batches_used)
  ├─ P5: context.p5_output (+ waste scores)
  ├─ P6: context.p6_output (ranked, top-K)
  └─ P7: context.final_bundles (List[BundleOutput])
  │
  ▼
_bundle_cache["BHX-HCM001"] = {bundles, generated_at}
  │
  ▼
HTTP Response: List[BundleOutput] as JSON
```

### 11.2 Agent Bundle Generation

```text
HTTP GET /bundles/BHX-HCM001?agent=true
  │
  ▼
run_b2b_agent(store_id, top_k=10)
  ├─ get_urgent_inventory(store_id, top_n=25)  → P1 batches (no LLM)
  └─ Build ingredient_urgency dict + inject into prompt
  │
  ▼
graph.ainvoke({messages: [HumanMessage(prompt)]})
  ├─ LLM: search_recipes_from_ingredients(ingredient_ids, ingredient_urgency)
  ├─ LLM: check_feasibility_and_substitute(recipe, inventory) × N
  ├─ LLM: query_ontology(missing_ingredient)  [if needed]
  └─ LLM: finalize_bundles(recipe_ids, store_id, top_k)
               ├─ run_p5(enriched_recipes, sku_lookup)
               ├─ run_p6(p5_output, store_id, top_k)
               └─ run_p7(p6_output, sku_lookup, store_id)
  │
  ▼
Extract List[BundleOutput] from finalize_bundles ToolMessage
  │
  ▼
HTTP Response: List[BundleOutput] as JSON
```

### 11.3 Consumer Chat Flow

```text
HTTP POST /consumer/chat {message, thread_id, allergies}
  │
  ▼
consumer_graph.chat(message, thread_id, user_allergies)
  ├─ MemorySaver loads state for thread_id (empty on first message)
  ├─ Inject user context (allergies, dietary preferences) on first turn
  │
  ▼
create_react_agent.ainvoke(messages, config={thread_id})
  │
  ├─ Discovery: resolve_ingredient_names
  │             → get_user_urgent_ingredients
  │             → find_recipes_for_consumer
  │             → adjust_recipe_for_user  [if allergies present]
  │
  └─ Shopping:  get_recipe_by_name
                → get_remaining_ingredients
                → get_ingredient_suggestions  [if missing items]
  │
  ▼
MemorySaver persists updated state for thread_id
  │
  ▼
HTTP Response: {reply: string, thread_id: string}
```

---

## 12. Reference Data

### 12.1 Inventory Coverage

| Category | SKU Count | Sample Ingredients |
| --- | --- | --- |
| fresh_meat | 25 | thit_heo, thit_ga, thit_bo, thit_vit, trung_ga |
| fresh_seafood | 12 | tom, ca_hoi, muc, ngheu, cua |
| fresh_produce | 21 | ca_chua, hanh_tay, rau_muong, gia_do, nam |
| processed | 22 | nuoc_mam, dau_an, sa_te, banh_pho, bun |
| **Total** | **80+** | |

### 12.2 Recipe Coverage

40+ Vietnamese dishes across six cooking categories:

| Category | Examples |
| --- | --- |
| Kho (braised) | thit_kho_tau, ca_kho_to, trung_kho_thit |
| Xao (stir-fry) | bo_xao_hanh, muc_xao_sa_ot, rau_xao_toi |
| Canh (soup) | canh_chua, pho, bun_bo_hue, bun_rieu |
| Chien (fried) | ca_chien, cha_gio, trung_chien |
| Luoc (boiled) | thit_luoc, rau_luoc, tom_luoc |
| Nuong (grilled) | suon_nuong, ca_nuong |

---

## 13. Testing Strategy

### 13.1 Test Matrix

| File | Coverage | Key Assertions |
| --- | --- | --- |
| `test_p1_priority.py` | P1 scoring | Category decay rates, urgency thresholds, top_n selection |
| `test_p2_retrieval.py` | P2 retrieval | Inverted index matching, urgency coverage formula |
| `test_p3_feasibility.py` | P3 feasibility | FEFO allocation, substitution, completeness threshold |
| `test_p5_waste.py` | P5 waste | Score computation, normalization across candidates |
| `test_p6_ranking.py` | P6 ranking | Weighted scoring, substitute penalty, ordering |
| `test_p7_pricing.py` | P7 pricing | Discount bounds, margin floor, urgency flag enrichment |
| `test_allocation.py` | FEFO engine | Strict/approx/best, multi-batch, deviation bounds |
| `test_pipeline_integration.py` | Full P1–P7 | End-to-end with mock data, 10 bundles returned |
| `test_b2b_agent.py` | B2B agent | Tool wrapping, graph routing, finalize_bundles |
| `test_consumer_agent.py` | Consumer | Multi-turn state, discovery mode, shopping mode tools |
| `test_agent_integration.py` | Integration | Tool calls, urgency flag propagation |

**Expected: 96+ tests passing.**

### 13.2 Fixture Strategy

All tests use deterministic mock data from `tests/fixtures/`:

- `mock_inventory.json` — Batches with realistic expiry dates and quantities
- `mock_skus.json` — Product definitions aligned with recipe requirements
- `mock_recipes.json` — Recipe definitions used by agent tools
- `mock_user_inventory.json` — Consumer home inventory scenarios

`conftest.py` provides shared fixtures: `mock_connector`, `pipeline_context`, `repo`.

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

---

## 14. Deployment

### 14.1 Docker

```bash
# Backend only
docker build -t freshroute .
docker run -p 8000:8000 --env-file .env freshroute

# Backend + Frontend
docker-compose up
```

`Dockerfile` uses `python:3.13-slim`, installs via `pip install -r requirements.txt`, runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

`docker-compose.yml` starts both services with the frontend connected to the backend via `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### 14.2 Environment Variables

| Variable | Default | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | required | FPT AI Factory key |
| `OPENAI_MODEL` | `gpt-oss-120b` | Any FPT-supported model ID |
| `TEMPERATURE` | `0.3` | LLM sampling temperature |
| `DEFAULT_CONNECTOR` | `mock` | `mock` (JSON fixtures) or `postgres` |
| `DATABASE_URL` | — | PostgreSQL for events and metrics |
| `FIREBASE_PROJECT_ID` | `freshroute-hackathon` | Firestore P6 weights cache |
| `P1_TOP_N` | `20` | Batches scored by P1 |
| `P2_TOP_K` | `20` | Recipe candidates from P2 |
| `P6_TOP_K` | `10` | Final ranked bundles |
| `BUNDLE_CACHE_TTL_SECONDS` | `3600` | Bundle cache lifetime (seconds) |

### 14.3 Logging

Rotating file logger at `logs/freshroute.log` (10 MB max, 5 backups) plus console output. Level controlled by `LOG_LEVEL` env var (default `INFO`).

### 14.4 Scaling Considerations

| Component | Current | Production path |
| --- | --- | --- |
| `DataRepository` | Process-local (static data) | No change needed — data is read-only |
| `_bundle_cache` | Process-local dict | Replace with Redis for multi-worker |
| `MemorySaver` (consumer chat) | In-memory | Replace with `AsyncPostgresSaver` or `AsyncRedisSaver` |
| LLM calls | Synchronous within LangGraph | Keep `recursion_limit` conservative (≤ 80) |
| Frontend | Fetches backend at request time | Add CDN or Next.js caching headers for combo pages |
