# B2B Agent — Architecture, Logic, and Failure Diagnosis

## 1. The Pipeline Context (P1 → P7)

The deterministic pipeline is the backbone. The agent wraps and partially replaces it.

```
P1 (Priority Scoring)
  ↓  batches × sales_history × sku_lookup  →  List[P1Output] sorted by priority_score
P2 (Recipe Retrieval)
  ↓  inverted_index × urgency scores  →  top-K candidate recipes
P3 (Feasibility Validation)
  ↓  FEFO allocation per ingredient × substitute_groups  →  feasible recipes with ingredient_status
P5 (Waste Scoring)
  ↓  value_rescued = priority × cost_per_gram × qty_taken_g  →  waste_score_normalized
P6 (Multi-objective Ranking)
  ↓  w1·urgency + w2·completeness + w3·waste − w4·deviation − penalty  →  ranked list
P7 (Dynamic Pricing)
  ↓  discount = 5%–30% constrained by weighted min_margin  →  List[BundleOutput]
```

Key structural facts:
- P3 runs **FEFO packet-based allocation** (`allocate_fefo`). Batches need `unit_count` and `pack_size_g` — not just `remaining_qty_g`.
- P5 scores waste from `matched_ingredients[].priority_score` × `sku_lookup[sku_id].cost_price`.
- P7 builds `BundleOutput` from `ingredient_status[].batches_used[].sku_id`.

---

## 2. B2B Agent Flow

```
run_b2b_agent(store_id, top_k)
  │
  ├─ get_urgent_inventory(store_id, top_n=25)   ← P1 run (or cached)
  │    returns: [{batch_id, ingredient_id, expiry_days, remaining_qty_g, priority_score, urgency_flag}]
  │
  ├─ Build prompt with urgent_context + ingredient_urgency dict
  │
  └─ LangGraph ainvoke → MessagesState loop
        ┌─────────────────────────────────────────────────────────┐
        │  call_agent (LLM node)                                  │
        │    - prepends SystemMessage only on turn 1              │
        │    - calls FPT LLM (OpenAI-compatible endpoint)         │
        │    - runs _recover_tool_call_from_text if no tool_calls │
        └─┬──────────────────────────────────────────────────────┘
          │ tool_calls?  →  ToolNode
          │               (search / check_feasibility / query_ontology / finalize_bundles)
          │ finalize done?  →  END
          └───────────── no finalize  →  back to agent
```

**Intended call sequence:**
1. `search_recipes_from_ingredients(ingredient_ids, ingredient_urgency)` — urgency-weighted P2 scoring
2. `check_feasibility_and_substitute(recipe)` — per-recipe FEFO feasibility (P3 equivalent)
3. `query_ontology(ingredient_id, relation)` — substitute lookup (optional)
4. `finalize_bundles(recipe_ids, store_id, top_k)` — internally runs P5 → P6 → P7

**finalize_bundles internal flow:**
```
recipe_ids → recipe_lookup[id] → _check_feasibility(recipe, store_id)
           → run_p5(validated_recipes, sku_lookup)
           → run_p6(p5_output, store_id, ...)
           → run_p7(p6_output, sku_lookup, ...)
           → return JSON list of BundleOutput
```

---

## 3. Observed Behavior From Logs

| Run | Store | Tool Calls | finalize called | Bundles |
|-----|-------|-----------|-----------------|---------|
| 2026-04-16 13:46 | BHX-HCM001 | [] | No | 0 |
| 2026-04-16 14:14 | BHX-HCM123 | [] | No | 0 |
| 2026-04-16 15:47 | BHX-HCM123 | search→check→check→ontology→search→ontology→**finalize** | Yes | **0** |
| 2026-04-16 15:58 | BHX-HCM123 | 15 checks + 2 searches (no finalize) | No | 0 |
| 2026-04-16 16:10 | BHX-HCM123 | search→check→ontology→ontology→check→check→search→check→check→ontology→**finalize** | Yes | **5** ✓ |
| 2026-04-17 12:07 | BHX-HCM001 | 17 calls → **finalize** | Yes | **2** ✓ |
| 2026-04-17 12:12 | BHX-HCM001 | 12 calls (no finalize) | No | 0 |
| 2026-04-17 12:33 | BHX-HCM001 | search→check | No | 0 |
| 2026-04-17 12:38 | BHX-HCM001 | search→check→check→ontology→**finalize** | Yes | **2** ✓ |

Success rate: ~3/9 runs. finalize_bundles reached in ~4/9, but crashed on first attempt.

---

## 4. Confirmed Bugs

### Bug 1: FPT LLM never emits native tool_calls (100% fallback rate)

**Evidence:** Every single LLM response triggers:
```
[fallback] Recovering tool call '...' from text content
```

The FPT model returns tool arguments as raw JSON text (e.g. `{"recipe_id": "R007", ...}`) instead of the OpenAI `tool_calls` structure. The `_recover_tool_call_from_text` fallback catches this and reconstructs an `AIMessage` with proper `tool_calls`.

**Impact:** The recovery is schema-based — it checks which tool's `required` fields are a subset of the JSON keys. If two tools share the same required key names, the first match wins. This can silently route the wrong tool.

---

### Bug 2 (Root Cause): LLM passes `full_inventory` without `unit_count` / `pack_size_g`

**Evidence (log line ~3586):**
```python
[llm_think] {"recipe": {...}, "full_inventory": [
  {"batch_id": "BATCH-0077", "ingredient_id": "ot_chuong", "expiry_days": 1, "remaining_qty_g": 500},
  ...
]}
```

The LLM constructs `full_inventory` from the urgent context in its prompt. That context has only `batch_id`, `ingredient_id`, `expiry_days`, `remaining_qty_g`, `priority_score`, `urgency_flag` — **no `unit_count`, no `pack_size_g`**.

`allocate_fefo` then runs:
```python
packs_in_batch = batch.get("unit_count", 0)   # → 0
if packs_in_batch <= 0:
    continue                                    # batch skipped entirely
```

**Every batch is skipped. Allocation always returns `feasible=False`.** The tool returns `completeness_score=0.0, feasible=False` for every recipe. The LLM sees no feasible recipes and outputs a text summary, causing the graph to exit without calling `finalize_bundles`.

This is the primary reason for `finalize_bundles_called=False` in most runs.

**Note:** When the LLM does NOT pass `full_inventory` (uses the default `None`), the tool correctly falls back to `connector.get_batches(store_id)` which has all required fields.

---

### Bug 3: `finalize_bundles` crashed on first execution

**Evidence (log line 1781):**
```
finalize_bundles called: recipe_ids=['R002', 'R002', 'R038', 'R004', 'R005']
finalize_bundles: 5/5 recipes passed allocation
finalize_bundles error: 'priority_score'
```

5 recipes passed allocation, then crashed with a `KeyError: 'priority_score'` before returning bundles. The error was caught by the outer try-except and returned as `{"error": "Finalize failed: 'priority_score'"}`. The result extraction in `run_b2b_agent` checks `isinstance(parsed, list)` — a dict is not a list, so `bundles=0`.

The crash source was in the P5 → P6 pipeline path inside `finalize_bundles`. The `matched_ingredients` structure built there may have been missing `priority_score` in an earlier version of the code (line numbers shifted between April 16 and current).

---

### Bug 4: System prompt disappears after turn 1

```python
# In call_agent:
if len(messages) == 1 and isinstance(messages[0], HumanMessage):
    messages = [SystemMessage(content=B2B_SYSTEM_PROMPT)] + messages
```

On all subsequent LLM calls (turns 2, 3, 4...) the system prompt is NOT included. The LLM gets only the conversation history with tool results but loses its operational instructions. This explains why the model sometimes drifts — calling `search_recipes_from_ingredients` a second time, or outputting a text summary instead of `finalize_bundles`.

---

### Bug 5: Agent exits after only 2 messages (LLM outputs plain text)

**Evidence (multiple runs):** `Agent completed with 2 messages`, `Tool calls: []`

When the LLM responds with prose ("Dựa trên phân tích...") instead of a JSON tool call, `_recover_tool_call_from_text` fails to match any tool (content doesn't start with `{`), `route_after_agent` returns `END`, and the graph terminates immediately.

**Root cause:** The FPT model ignores the "STRICT RULES — call exactly one tool" instruction, especially when the system prompt is missing on later turns (Bug 4).

---

### Bug 6: `finalize_bundles` called with duplicate recipe IDs

**Evidence (log line 1774):**
```
recipe_ids=['R002', 'R002', 'R038', 'R004', 'R005']
```

R002 appears twice. `finalize_bundles` iterates the list and processes the same recipe twice. Both pass allocation and enter P5 → P6 → P7, producing two nearly identical bundles for the same recipe. This inflates results and wastes ranking slots.

---

### Bug 7: Agent under-delivers on bundle count

**Evidence:**
- Run 12:07 (top_k=20): finalizes with only `recipe_ids=['R007', 'R039']` → 2 bundles
- Run 12:38 (top_k=10): finalizes with only `recipe_ids=['R006', 'R027']` → 2 bundles

The LLM stops checking feasibility long before reaching `top_k` feasible recipes. This is partially caused by Bug 2 (feasibility checks always fail when LLM passes full_inventory) — the LLM gives up after a few "infeasible" results.

---

### Bug 8: All priority_scores = 0 in some store runs

**Evidence (log line ~3238):**
```python
"ingredient_urgency": {"thit_heo": 0, "thit_heo_xay": 0, ...}  # all zero
```

For store `BHX-HCM123` in an earlier run, P1 returned all scores as 0. `get_urgent_inventory` cold-path runs `run_p1` and returns `urgency_flag="WATCH"` for everything. The prompt tells the LLM these are urgent but all scores are 0 — contradictory data. The LLM ignores urgency weighting because all weights are equal (0.0).

Likely cause: cold P1 cache + P1 scoring edge case returning 0 for all batches.

---

### Bug 9: `check_feasibility_and_substitute` called repeatedly in isolation (no `full_inventory=None` enforcement)

The tool signature allows `full_inventory` as an optional param:
```python
def check_feasibility_and_substitute(recipe: dict, full_inventory: List[dict] = None) -> dict:
```

The LLM description says nothing about not passing `full_inventory`. The LLM "helpfully" constructs it from the prompt context, which causes Bug 2. There is no guard preventing this.

---

### Bug 10: Result extraction assumes `messages[i+1]` is always the ToolMessage

```python
for i, msg in enumerate(messages):
    if isinstance(msg, AIMessage) and any(tc.get("name") == "finalize_bundles" ...):
        if i + 1 < len(messages):
            tool_resp = messages[i + 1]
            raw = getattr(tool_resp, "content", "")
```

This assumes the ToolMessage is exactly one position after the AIMessage. LangGraph's `ToolNode` may append multiple ToolMessages if the AIMessage contained multiple tool calls. If `finalize_bundles` is not the first tool call in that AIMessage, `messages[i+1]` would be the wrong tool's response.

---

## 5. Questions for GPT to Help Break Down

> **Context to share:** FPT model (OpenAI-compatible), LangGraph StateGraph, Python async, Vietnamese food domain. The agent is failing ~67% of the time, mostly because `finalize_bundles` is never called.

1. **Bug 2 fix strategy**: The LLM constructs `full_inventory` from the prompt context, omitting required fields (`unit_count`, `pack_size_g`). Should we (a) remove `full_inventory` from the tool signature entirely and always use `connector.get_batches`, (b) add a validator inside the tool that ignores `full_inventory` if it lacks required fields, or (c) restructure the tool description to explicitly forbid passing `full_inventory`? Which approach survives an unreliable LLM that ignores instructions?

2. **System prompt strategy**: What's the correct pattern for injecting a system prompt in LangGraph `MessagesState` so it persists across all LLM calls without being doubled? Is the standard pattern to use a `SystemMessage` as the first element of a separate `messages` var on each node call, or to use a custom state with a dedicated `system_prompt` field?

3. **Fallback tool matching**: `_recover_tool_call_from_text` uses `required_fields.issubset(json_keys)` to identify which tool was called. If the model outputs `{"recipe_ids": [...], "store_id": "..."}` it will match `finalize_bundles`. If it outputs `{"ingredient_id": "x", "relation": "substitute"}` it will match `query_ontology`. What's a more robust disambiguation strategy — e.g., using tool name as a required field in the JSON output, or using LLM-side structured output mode?

4. **Termination condition**: The agent should call `finalize_bundles` after collecting 3–10 feasible recipes. How do you enforce this in LangGraph without relying on the LLM to decide? For example: should we add a custom state counter and a conditional edge that forces `finalize_bundles` when `feasible_count >= min_k`?

5. **`route_after_agent` END on plain text**: When the LLM outputs prose instead of a tool call, the graph exits. Should `route_after_agent` route to a "reprompt" node instead of `END` in this case, retrying with an explicit "you must call a tool" message? Is there a standard LangGraph pattern for this?

6. **Duplicate recipe_ids in finalize_bundles**: The LLM passes `['R002', 'R002', ...]`. Should `finalize_bundles` deduplicate `recipe_ids` at entry, or should the prompt be updated to say "each recipe_id must appear once"? Is deduplication always safe (same recipe won't be ranked differently on a second pass)?

7. **`finalize_bundles` under-delivery**: The LLM finalizes with 2 recipes when `top_k=10`. Is the right fix to (a) enforce a minimum number of feasibility checks before allowing `finalize_bundles`, (b) change the prompt threshold from "3–10 feasible" to "at least min(top_k, total_searched)", or (c) loop `search_recipes` automatically until enough candidates are found?

8. **tool_factory / make_tool schema issue**: `make_tool` uses `@functools.wraps(fn)` inside `@tool`. Does LangChain's `@tool` correctly derive the args_schema from the wrapped function's annotations (via `__wrapped__`)? If not, the schema is `(*args, **kwargs)` → required=[] → fallback recovery never matches these tools. How should `make_tool` be written to preserve schema introspection?

9. **P1 priority_score = 0 for all batches**: In some runs all urgency scores are 0. Should the agent refuse to run if all urgency scores are below a threshold (say < 0.05), or fall back to the deterministic pipeline? Is a "all-zero urgency" case a bug in P1 or a valid state (e.g., all stock has many days left)?

10. **Context blowup from `full_inventory` in message history**: When the LLM includes `full_inventory` in a tool call, the entire inventory JSON (potentially hundreds of batches) gets appended to `MessagesState`. After 10 tool calls, the context window fills with redundant inventory data. What's the LangGraph-idiomatic way to summarize or truncate tool result messages to prevent this? (e.g., `trim_messages`, custom message reducer, or tool result post-processing node)
