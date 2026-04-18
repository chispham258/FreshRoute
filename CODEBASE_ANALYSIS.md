# CODEBASE_ANALYSIS

Code-level walkthrough of the FreshRoute system. Covers module responsibilities, key functions, data flow, and known issues.

---

## 1. Module Map

```text
app/
├── agent/
│   ├── b2b/
│   │   ├── graph.py        custom StateGraph, tool recovery, run_b2b_agent()
│   │   ├── tools.py        b2b_langchain_tools list + make_tool wrappers
│   │   └── prompt.py       B2B_SYSTEM_PROMPT (Vietnamese, store operator context)
│   ├── consumer/
│   │   ├── graph.py        custom StateGraph, MemorySaver, chat(), suggest()
│   │   ├── tools.py        consumer_langchain_tools list + make_tool wrappers
│   │   ├── prompt.py       CONSUMER_SYSTEM_PROMPT (Vietnamese, home cook context)
│   │   └── state.py        (unused — agent uses MessagesState from LangGraph)
│   ├── shared/
│   │   ├── tool_factory.py make_tool(fn, description) → @tool with JSON output
│   │   └── ontology.py     query_ontology(), are_substitutes()
│   └── tools.py            all shared tool implementations
│
├── core/
│   ├── pipeline/
│   │   ├── orchestrator.py run_pipeline() entry point
│   │   ├── base.py         PipelineContext, PipelineStage ABC, PipelineChain
│   │   ├── p1_priority.py  run_p1() — urgency scoring
│   │   ├── p2_retrieval.py run_p2() — recipe candidate matching
│   │   ├── p3_feasibility.py run_p3() — FEFO + substitution
│   │   ├── p5_waste.py     run_p5() — waste impact scoring
│   │   ├── p6_ranking.py   run_p6() — multi-objective ranking
│   │   ├── p7_pricing.py   run_p7() — dynamic pricing → BundleOutput
│   │   ├── p1_cache.py     module-level dict cache for P1 output
│   │   └── p8_tracking.py  exists but NOT wired into pipeline chain
│   ├── engine/
│   │   ├── allocation.py   allocate_fefo(batches, required_g, strategy)
│   │   └── waste.py        waste scoring helpers
│   ├── data/
│   │   ├── repository.py   DataRepository singleton — canonical data source
│   │   ├── skus.py         93 SKU definitions
│   │   ├── recipes.py      40 Vietnamese recipe definitions
│   │   ├── ingredient_aliases.json   178 aliases → ingredient_id
│   │   ├── substitute_groups.json    29 substitution groups
│   │   ├── category_margins.json     min margins by category
│   │   └── default_weights.json      P6 cold-start weights
│   └── models/
│       ├── bundle.py       BundleOutput, BundleIngredientDisplay
│       ├── inventory.py    ProductSKU, ProductBatch, P1Output
│       └── recipe.py       Recipe model
│
├── api/
│   ├── bundles.py          GET /bundles/{store_id} with agent/pipeline paths
│   ├── admin.py            GET/POST /api/admin/{combos,inventory,warmup,accept,reject}
│   ├── consumer.py         POST /consumer/chat, /suggest; GET /consumer/api/customer/combos
│   ├── health.py           GET /health
│   ├── tracking.py         bundle event tracking (partially implemented)
│   └── metrics.py          observability (stub)
│
├── integrations/
│   ├── llm.py              FPTChatOpenAI(ChatOpenAI) adapter + get_llm()
│   ├── connectors/
│   │   ├── base.py         StoreConnector ABC
│   │   └── mock.py         MockConnector — reads tests/fixtures/batches.json
│   └── db/
│       ├── firestore.py    Firestore client (P6 weights storage)
│       └── postgres.py     PostgreSQL stub (unused)
│
├── main.py                 FastAPI app, CORS, router registration, lifespan
├── config.py               Pydantic BaseSettings (OPENAI_API_KEY, etc.)
└── dependencies.py         FastAPI Depends: get_connector(), get_llm()
```

---

## 2. Agent Code

### 2.1 `app/agent/tools.py` — Shared Tool Implementations

All tool logic for both agents lives here. Key functions:

**`resolve_ingredient_names(user_inputs: List[str]) → List[dict]`**

Looks up each input in `DataRepository.ingredient_aliases()`. Returns `[{input, ingredient_id, resolved: bool}, ...]`. Unresolved inputs get `ingredient_id: null, resolved: false`.

**`find_recipes_for_consumer(available_ingredients, urgent_ingredients, allergies, top_k) → List[dict]`**

Reads from `DataRepository.get().recipes()` (canonical source — not from any fixture file).

Scoring per recipe:

```python
urgent_matches = recipe_ing_set & urgent_ids
normal_matches = (recipe_ing_set & available_ids) - urgent_ids
score = len(urgent_matches) * 3 + len(normal_matches)
```

Allergen exclusion: before scoring, checks if any required (non-optional) ingredient is in `allergy_set`. If so, checks whether a safe substitute is available from ontology. Excludes recipe entirely if no safe path exists.

Returns recipes with `score > 0`, sorted descending, sliced to `top_k`. Each result includes `ingredients` (full ingredient list), `urgent_used`, `available_used` — the latter two are used by `_enrich_suggestions()` to set the `have` flag.

**`get_remaining_ingredients(recipe_id, available_ingredients) → dict`**

Uses `DataRepository.recipe_lookup()` to fetch recipe by ID. For each ingredient not in `available_ingredients`, looks up price from `DataRepository.ingredient_sku_lookup()` (keyed by `ingredient_id`). Returns `{to_buy: [...], already_have: [...]}`.

**`note_allergy(allergy_names: List[str]) → dict`**

Resolves allergy names via `resolve_ingredient_names`, returns `{allergy_ids, unresolved, note}`. The note instructs the LLM to pass `allergy_ids` to future tool calls. Designed to be called once and persist as a `ToolMessage` in the conversation history — a "tool-as-memory" pattern.

**`get_ingredient_display_name(ingredient_id: str) → str`**

Reverses the alias map to get a display name. Falls back to `ingredient_id.replace("_", " ")` if no alias found.

**`get_urgent_inventory(store_id, top_n) → List[dict]`**

Runs P1 scoring on the store's inventory and returns top-n urgent items with their P1 priority scores. Used by B2B agent for context injection.

### 2.2 `app/agent/b2b/graph.py`

**`_recover_tool_call_from_text(response, tools)`**

Handles two text formats the FPT model emits instead of structured tool_calls:

- Format 1: raw JSON `{"recipe_ids": [...], "store_id": "..."}` — parsed with `json.loads`, matched by checking required schema keys
- Format 2: Python call `finalize_bundles(recipe_ids=[...], store_id="...")` — matched by tool name regex, kwargs extracted with regex-based JSON conversion

If recovery succeeds, returns a new `AIMessage` with `tool_calls` set so the ToolNode can execute normally.

**`run_b2b_agent(store_id, top_k) → List[BundleOutput]`**

Entry point. Fetches urgent inventory, injects into system prompt, invokes the graph, extracts `BundleOutput` list from the last `finalize_bundles` ToolMessage.

`route_after_tools` checks if any tool in the last ToolNode batch had name `"finalize_bundles"` — if so, returns `END`; otherwise returns `"agent"` to continue the loop.

### 2.3 `app/agent/consumer/graph.py`

**`_parse_python_call_args(text) → dict | None`**

Uses `ast.parse(f"_f({text})", mode="eval")` to parse Python kwargs into a dict. Handles both single-quoted and double-quoted string values, nested dicts and lists. More robust than the regex approach used in the B2B agent for complex args like `find_recipes_for_consumer(available_ingredients=[{...}], ...)`.

**`_recover_tool_call_from_text(response, tools)`**

Same two-format approach as B2B, but Format 2 kwargs are parsed with `_parse_python_call_args` (AST) first, regex fallback second.

**`_extract_recipe_suggestions(messages) → list | None`**

Scans `messages` for:

1. `AIMessage` with `tool_calls` containing `find_recipes_for_consumer` → collects IDs
2. `ToolMessage` with `tool_call_id` in collected IDs → parses JSON content

Fallback: if no AIMessage tool_calls found, scans for `ToolMessage` with `name == "find_recipes_for_consumer"` (set by LangGraph ToolNode).

Returns `_enrich_suggestions(content)` or `None`.

**`_enrich_suggestions(raw) → list`**

Maps raw `find_recipes_for_consumer` output to the `recipe_suggestions` API shape. Sets `have: True` for ingredients whose ID is in `urgent_used | available_used` from the tool result.

**`chat(message, thread_id, user_context) → tuple[str, list|None, list|None]`**

Returns `(reply_text, shopping_list, recipe_suggestions)`. Both structured fields are extracted from conversation messages after the agent completes. `shopping_list` comes from the last `get_remaining_ingredients` ToolMessage.

---

## 3. Deterministic Pipeline

### 3.1 `app/core/pipeline/orchestrator.py`

`run_pipeline(store_id, connector, firestore_client, top_n, top_k_p2, top_k_p6)` builds a `PipelineContext`, assembles a `PipelineChain`, and executes stages in order.

`PipelineContext` carries all inputs and intermediate outputs:

```python
class PipelineContext:
    batches: List[dict]
    sales_history: dict
    sku_lookup: dict
    recipe_lookup: dict
    substitute_groups: dict
    # filled as pipeline runs:
    p1_output: List[P1Output]
    p2_output: List[dict]
    p3_output: List[dict]
    p5_output: List[dict]
    p6_output: List[dict]
    final_bundles: List[BundleOutput]
```

### 3.2 `app/core/engine/allocation.py`

`allocate_fefo(batches, required_g, strategy="best")` is the core allocation primitive.

Batches must be pre-sorted by `expiry_days` ascending (FEFO = earliest expiry first). The function iterates batches, calculates `packets_to_take = ceil or floor(remaining_needed / pack_size)`, and accumulates until `remaining_needed <= 0`.

`AllocationResult` fields:

- `packets_used`, `allocated_g`, `deviation` (abs ratio)
- `strategy`: `"strict"` or `"approx"`
- `feasible`: `allocated_g >= required_g and deviation <= 0.25`
- `batches_used`: `[{batch_id, packets_taken, grams_taken}]`

`best` strategy: run strict, check feasible. If not, run approx, return whichever has lower deviation.

### 3.3 `app/core/data/repository.py`

`DataRepository` is a singleton (`_instance` class variable). All data-loading methods have `@lru_cache(maxsize=1)` — called once per process lifetime.

Key methods and their sources:

| Method | Source |
| --- | --- |
| `recipes()` | `app/core/data/recipes.py` |
| `skus()` | `app/core/data/skus.py` |
| `ingredient_aliases()` | `ingredient_aliases.json` (flattened across all category keys) |
| `ingredient_sku_lookup()` | derived from `skus()`, keyed by `ingredient_id` |
| `sku_dict_lookup()` | derived from `skus()`, keyed by `sku_id` |
| `recipe_lookup()` | derived from `recipes()`, keyed by `recipe_id` |
| `substitute_groups()` | `substitute_groups.json` |

`ingredient_aliases.json` is a nested object by category (`proteins`, `vegetables`, `sauces_pantry`, etc.). The repository flattens it by iterating all category values. 178 total aliases after the most recent additions (common ingredients like `muối → muoi`, `tiêu → tieu`, `mì Ý → mi_y` that were previously missing).

---

## 4. API Layer

### 4.1 `app/api/consumer.py`

`ChatResponse` model:

```python
class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    shopping_list: Optional[List[ShoppingItem]] = None
    recipe_suggestions: Optional[List[RecipeSuggestion]] = None
```

`RecipeSuggestion` shape:

```python
class RecipeSuggestionIngredient(BaseModel):
    name: str
    have: bool = False
    optional: bool = False

class RecipeSuggestion(BaseModel):
    recipe_id: str
    name: str
    score: float = 0.0
    ingredients: List[RecipeSuggestionIngredient] = []
```

`consumer_chat()` endpoint unpacks the 3-tuple from `chat()`:

```python
reply, raw_sl, raw_suggestions = await chat(message=req.message, thread_id=req.thread_id, ...)
```

### 4.2 `app/api/admin.py`

`get_accepted_bundles(store_id)` returns combos that have been accepted. Currently backed by an in-memory dict (`_accepted_bundles`); no persistence.

`get_admin_combos()` tries B2B agent first, falls back to deterministic pipeline. Converts `BundleOutput` to `ComboResponse` (frontend-facing shape with `aiReason`, `confidence`, etc.).

### 4.3 Bundle Cache

`app/api/bundles.py` maintains a process-local `_bundle_cache: dict[str, dict]` with 6-hour TTL. Background refresh is scheduled at 3 hours. Cache is populated by any `/bundles/{store_id}` call and shared with `/api/admin/combos` when the pipeline path is taken.

---

## 5. Frontend Code

### 5.1 `frontend/src/app/customer/ai-chat/page.js`

Key state:

```javascript
messages: [{id, type, text, shoppingList?, recipeSuggestions?}]
allergies: string[]        // allergy chip list, sent with each message
allergyInput: string       // input field for adding chips
threadIdRef: useRef(...)   // stable across renders, not tied to re-render
```

**`RecipeSuggestionCard`** — expand/collapse per recipe:

```javascript
const [expanded, setExpanded] = useState(false);
// Collapsed: name + chevron
// Expanded: ingredient list with have/need indicators
//   green ● = user has it  |  gray ● + "cần mua" = user needs to buy
//   (optional) label for optional ingredients
```

**`ShoppingListPanel`** — selection-aware cart:

```javascript
const [selected, setSelected] = useState(() => new Set(items?.map(i => i.ingredient_id)));

// useEffect deselects allergen items when allergies chip list changes
useEffect(() => {
    setSelected(prev => {
        const next = new Set(prev);
        items?.forEach(item => {
            if (isAllergen(item)) next.delete(item.ingredient_id);
        });
        return next;
    });
}, [allergies]);
```

Cart adds only selected items to `localStorage` via `addItemToCart()` from `lib/cart.js`.

### 5.2 `frontend/src/lib/customerApi.js`

`sendConsumerChat({ message, threadId, allergies })` sends `allergies` only if non-empty. Maps response:

```javascript
return {
    reply: payload.reply,
    threadId: payload.thread_id,
    shoppingList: Array.isArray(payload.shopping_list) ? payload.shopping_list : null,
    recipeSuggestions: Array.isArray(payload.recipe_suggestions) ? payload.recipe_suggestions : null,
};
```

### 5.3 `frontend/src/lib/cart.js`

`addItemToCart(item)` and `getCart()` use `localStorage`. No backend persistence. `processPayment()` in `cart/page.js` is a mock (setTimeout + `clearCart()`).

---

## 6. LLM Integration

### 6.1 `app/integrations/llm.py`

`FPTChatOpenAI` extends `ChatOpenAI`. Overrides `_get_request_payload` to:

1. Build a `tool_call_id → tool_name` map from assistant messages
2. Inject `"name"` field into every tool-role message (FPT AI requires this; LangChain doesn't add it)
3. Ensure `content` is always a string

`get_llm()` returns a singleton `FPTChatOpenAI` instance, configured from `config.py` settings.

---

## 7. Known Issues and Gaps

### 7.1 Failing Tests (14)

- `test_b2b_agent.py::TestCheckFeasibilityWithPacketAllocation` (5 tests) — packet allocation metrics assertions fail; likely a mismatch between expected and actual `AllocationResult` fields
- `test_p6_ranking.py::test_run_p6_ranks` — `IndexError: list index out of range`; P6 output may be empty when input has fewer recipes than expected
- `test_pipeline_integration.py::test_full_pipeline` — asserts `len(bundles) > 0` but gets 0; P3 feasibility may be discarding all recipes with mock data

### 7.2 P8 Tracking Not Wired

`app/core/pipeline/p8_tracking.py` exists but is not in the `PipelineChain` in `orchestrator.py`. Admin accept/reject actions log to console but don't persist feedback anywhere.

### 7.3 In-Memory State Lost on Restart

- Bundle cache (`_bundle_cache`) — process dict
- P1 cache (`p1_cache`) — module-level dict
- Consumer conversation state (`MemorySaver`) — in-memory

All are lost on server restart. Production path: Redis for bundle/P1 cache, `AsyncPostgresSaver` for conversation state.

### 7.4 No Inventory Deduction

Bundles are recommended from inventory but no deduction happens when a combo is accepted or a shopping cart item is added. The same batch can appear in multiple simultaneous bundle recommendations.

### 7.5 Frontend Cart Is Local-Only

Cart state is in `localStorage`. No order API exists. `processPayment()` is a mock that clears the cart after a timeout.

### 7.6 Single-Store MockConnector

`MockConnector` reads `tests/fixtures/batches.json` for a hardcoded set of stores. Multi-store support requires real database integration.

### 7.7 Firestore Weights Not Fully Tested

P6 loads weights from Firestore if available, falls back to `default_weights.json`. The Firestore path has not been tested end-to-end in the current environment.
