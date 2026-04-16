# FreshRoute

**AI-powered food waste reduction for Vietnamese retail chains and home consumers.**

FreshRoute tackles the last-mile food waste problem: near-expiry perishables that supermarkets can't move fast enough and home cooks who don't know what to cook with what they have. It provides two tightly integrated solutions backed by the same AI pipeline.

---

## Features

### B2B — Store Bundle Engine

- Deterministic P1–P7 pipeline: scores every batch by urgency, retrieves Vietnamese recipes, checks feasibility with real inventory, applies FEFO allocation, ranks by multi-objective score, and computes margin-safe discounted pricing
- Optional LangGraph agent mode that reasons over the same data using an LLM (FPT AI Factory)
- 6-hour in-memory bundle cache with stale-while-revalidate background refresh
- Admin portal for reviewing, accepting, and rejecting AI-suggested combos

### Consumer — AI Cooking Assistant

- Multi-turn conversational agent (Vietnamese language) backed by LangGraph + MemorySaver
- **Discovery Mode**: user lists ingredients → agent finds recipes that prioritize near-expiry items
- **Shopping Mode**: user names a dish → agent computes the shopping list with quantities, costs, and substitutes
- Ingredient ontology with 29 Vietnamese cuisine substitution groups
- Customer portal for browsing discounted bundles from the store

### Frontend Portals (Next.js 16)

| Portal | Path | Description |
| --- | --- | --- |
| Admin | `/admin` | Inventory urgency list + AI combo suggestions (accept/reject) + analytics dashboard |
| Customer | `/customer` | Browse discounted bundles with ingredient details and cooking steps |
| AI Chat | `/customer/ai-chat` | Full conversational AI — discovery and shopping modes |

---

## Quick Start

### Requirements

- Python 3.13+ and [uv](https://docs.astral.sh/uv/) (or pip)
- Node.js 18+ (for frontend)
- FPT AI Factory key (agent/chat endpoints only; deterministic pipeline works without one)

### Backend

```bash
# Install dependencies
uv sync
# OR: pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Minimum for deterministic pipeline (no LLM key needed):
#   DEFAULT_CONNECTOR=mock

# Start server
uvicorn app.main:app --reload --port 8000
```

Swagger docs: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: <http://localhost:3000>

The frontend connects to the backend at `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`).

### Run Tests

```bash
python -m pytest tests/ -v
# Expected: 96+ passing
```

### Docker (both services)

```bash
docker-compose up
```

---

## API Reference

### B2B Bundle Recommendations

**`GET /bundles/{store_id}`**

Returns ranked, priced bundle recommendations for a store. Results are cached for 6 hours.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `limit` | int | 10 | Max bundles to return (1–10) |
| `agent` | bool | false | Use LangGraph B2B agent instead of deterministic pipeline |
| `force_refresh` | bool | false | Bypass cache and re-run pipeline |

```bash
# Deterministic pipeline (no LLM needed)
curl http://localhost:8000/bundles/BHX-HCM001

# Agent mode
curl "http://localhost:8000/bundles/BHX-HCM001?agent=true&limit=5"
```

**Response:**
```json
[
  {
    "bundle_id": "R017__BHX-HCM001__20260416",
    "recipe_id": "R017",
    "recipe_name": "Vịt kho sả ớt",
    "rank": 1,
    "final_score": 1.14,
    "urgency_coverage_score": 1.19,
    "completeness_score": 1.30,
    "waste_score_normalized": 0.76,
    "original_price": 145000,
    "discount_rate": 0.156,
    "final_price": 122339,
    "gross_profit": 18339,
    "gross_margin": 0.15,
    "ingredients": [
      {
        "ingredient_id": "thit_vit",
        "sku_id": "SKU-M011",
        "product_name": "Thịt vịt tươi",
        "qty_taken_g": 500,
        "item_retail_price": 95000,
        "is_substitute": false,
        "urgency_flag": "CRITICAL"
      }
    ],
    "store_id": "BHX-HCM001"
  }
]
```

**`POST /bundles/{store_id}/refresh`** — Trigger async background cache refresh.

**`GET /bundles/{store_id}/cache-status`** — Cache age, bundle count, validity.

---

### Admin Portal

**`GET /api/admin/combos?storeId={id}`** — AI-suggested combos formatted for admin review (name, discount %, ingredients, pricing, AI reasoning).

**`GET /api/admin/inventory?storeId={id}`** — Inventory items sorted by urgency with days-remaining and status flags.

**`POST /api/admin/combos/{combo_id}/accept`** — Accept a combo for customer promotion.

**`POST /api/admin/combos/{combo_id}/reject`** — Reject with optional reason.

---

### Consumer Assistant

**`POST /consumer/chat`** — Multi-turn conversation. State persists per `thread_id`.

```bash
# Discovery mode — user has ingredients
curl -X POST http://localhost:8000/consumer/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi có thịt heo sắp hết hạn, cà chua và trứng. Nấu gì?",
    "thread_id": "session-001",
    "allergies": ["tôm"]
  }'

# Shopping mode — user knows the dish
curl -X POST http://localhost:8000/consumer/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi muốn nấu Phở. Đã có thịt bò và hành.",
    "thread_id": "session-002"
  }'

# Follow-up in the same session
curl -X POST http://localhost:8000/consumer/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Có thể thay thịt heo bằng gì khác không?", "thread_id": "session-001"}'
```

**`POST /consumer/suggest`** — Stateless one-shot recipe suggestion.

```bash
curl -X POST http://localhost:8000/consumer/suggest \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["thịt heo", "cà chua", "trứng gà"], "allergies": ["tôm"], "top_k": 3}'
```

**`GET /consumer/api/customer/combos?storeId={id}`** — Customer-facing bundle view (images, tags, cooking steps).

---

### Other Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | GET | Health check (`{"status": "ok"}`) |
| `/events` | POST | Log impression / click / purchase event (async, 202) |
| `/metrics/{store_id}` | GET | Waste reduction KPIs and bundle performance (requires PostgreSQL) |

---

## Project Structure

```
app/
├── core/                    Pure domain logic — framework-free, fully testable
│   ├── pipeline/            P1–P7 pipeline stages + orchestrator
│   │   ├── base.py          PipelineStage ABC, PipelineContext, PipelineChain
│   │   ├── orchestrator.py  run_pipeline() public entry point
│   │   ├── p1_priority.py   Inventory risk scoring
│   │   ├── p2_retrieval.py  Recipe candidate retrieval
│   │   ├── p3_feasibility.py Feasibility check + FEFO allocation
│   │   ├── p5_waste.py      Waste value scoring
│   │   ├── p6_ranking.py    Multi-objective ranking
│   │   └── p7_pricing.py    Dynamic pricing with margin floor
│   ├── engine/
│   │   └── allocation.py    Packet-based FEFO allocation engine
│   ├── data/
│   │   ├── repository.py    DataRepository singleton (LRU-cached lookups)
│   │   ├── skus.py          80+ Vietnamese product SKU definitions
│   │   ├── recipes.py       40+ Vietnamese recipe definitions
│   │   ├── substitute_groups.json   Ingredient substitution ontology
│   │   ├── ingredient_aliases.json  Vietnamese name → ingredient_id map
│   │   ├── default_weights.json     P6 ranking weights
│   │   └── category_margins.json    Minimum margin by product category
│   └── models/
│       ├── inventory.py     ProductSKU, ProductBatch, P1Output
│       ├── bundle.py        BundleOutput, BundleIngredientDisplay, BundleEvent
│       └── recipe.py        Recipe, RecipeRequirement
│
├── agent/                   LangGraph agents
│   ├── shared/
│   │   ├── tool_factory.py  make_tool() — wrap functions as LangChain tools
│   │   └── ontology.py      query_ontology(), are_substitutes()
│   ├── b2b/                 Store bundle agent
│   │   ├── graph.py         Custom StateGraph with finalize_bundles routing
│   │   ├── tools.py         search_recipes, check_feasibility, finalize_bundles
│   │   └── prompt.py        Vietnamese B2B system prompt
│   ├── consumer/            Home cooking agent
│   │   ├── graph.py         create_react_agent + MemorySaver checkpointer
│   │   ├── tools.py         Consumer LangChain tools
│   │   ├── prompt.py        Vietnamese consumer system prompt
│   │   └── state.py         ConsumerAgentState TypedDict
│   └── tools.py             Core tool implementations shared by both agents
│
├── api/                     FastAPI route handlers
│   ├── bundles.py           /bundles — pipeline + cache management
│   ├── consumer.py          /consumer — chat, suggest, customer combos
│   ├── admin.py             /api/admin — combos, inventory, accept/reject
│   ├── health.py            /health
│   ├── tracking.py          /events
│   └── metrics.py           /metrics
│
├── integrations/
│   ├── llm.py               FPTChatOpenAI wrapper + get_llm() factory
│   ├── connectors/          StoreConnector ABC + MockConnector
│   └── db/                  Firestore + PostgreSQL clients
│
├── config.py                Pydantic BaseSettings (.env-driven)
├── dependencies.py          FastAPI dependency injection
└── main.py                  App entry point + logging setup

frontend/
├── src/
│   ├── app/
│   │   ├── admin/page.js         Admin portal
│   │   └── customer/
│   │       ├── page.js           Customer bundle browser
│   │       ├── ai-chat/page.js   AI chat interface
│   │       └── cart/page.js      Shopping cart
│   ├── components/admin/
│   │   ├── AnalyticsDashboard.jsx  Revenue and bundle metrics
│   │   └── ComboDetailModal.jsx    Combo detail view
│   └── lib/api.js                  Centralized API client

tests/
├── fixtures/                Mock inventory, SKUs, recipes, user inventory
├── conftest.py              Shared pytest fixtures
└── test_*.py                96+ tests across pipeline, allocation, and agents

scripts/
├── generate_mock_data.py    Generate test fixtures
├── build_inverted_index.py  Rebuild ingredient → recipe index
└── build_mock_user_inventory.py
```

---

## Configuration

All configuration is via environment variables (or `.env`):

| Variable | Default | Required | Description |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | — | Agent/chat endpoints | FPT AI Factory key |
| `OPENAI_MODEL` | `gpt-oss-120b` | Agent/chat endpoints | Model ID |
| `TEMPERATURE` | `0.3` | No | LLM sampling temperature |
| `DEFAULT_CONNECTOR` | `mock` | No | `mock` (no DB) or `postgres` |
| `DATABASE_URL` | — | Metrics/events | PostgreSQL connection string |
| `FIREBASE_PROJECT_ID` | `freshroute-hackathon` | No | Firestore weights cache |
| `P1_TOP_N` | `20` | No | Batches scored by P1 |
| `P2_TOP_K` | `20` | No | Recipe candidates from P2 |
| `P6_TOP_K` | `10` | No | Final ranked bundles |
| `BUNDLE_CACHE_TTL_SECONDS` | `3600` | No | Bundle cache lifetime |

**Minimal `.env` (no LLM, no DB):**

```bash
DEFAULT_CONNECTOR=mock
```

**Full `.env` (all features):**

```bash
OPENAI_API_KEY=your-fpt-ai-key
OPENAI_MODEL=gpt-oss-120b
TEMPERATURE=0.3
DEFAULT_CONNECTOR=mock
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/freshroute
# FIREBASE_PROJECT_ID=freshroute-hackathon
```

---

## Key Concepts

### P1–P7 Pipeline

The deterministic path scores every batch and returns priced bundles with zero LLM calls:

```text
P1 Priority Scoring  →  P2 Recipe Retrieval  →  P3 Feasibility (FEFO)
  →  P5 Waste Scoring  →  P6 Multi-Objective Ranking  →  P7 Dynamic Pricing
```

Each stage is a `PipelineStage` (Chain of Responsibility) reading from and writing to a shared, immutable `PipelineContext`. Stage failures are captured without halting the chain.

### Score-Based Urgency

Urgency comes from a composite P1 priority score blending expiry speed, supply/demand ratio, and sell-through rate — not raw days-to-expiry alone:

| Flag | Score | Discount |
| --- | --- | --- |
| `CRITICAL` | ≥ 0.80 | Move at any discount |
| `HIGH` | ≥ 0.65 | Aggressive discount |
| `MEDIUM` | ≥ 0.50 | Standard discount |
| `WATCH` | < 0.50 | Monitor only |

### Packet-Based FEFO Allocation

Inventory is allocated in discrete packets (packs), not continuous grams, respecting First-Expiry-First-Out order:

```python
result = allocate_fefo(batches, required_g=1000, strategy="best")
# → AllocateResult(allocated_g=1000, deviation=0.0, feasible=True)
```

Three strategies: `strict` (ceil), `approx` (floor), `best` (strict → approx fallback if deviation > 25%).

### Ingredient Ontology

29 substitution groups for Vietnamese cuisine. Used in P3 feasibility, allergy handling, and agent tool calls:

```python
query_ontology("thit_heo", relation="substitute")
# → {"substitutes": ["thit_ga", "thit_bo", "thit_de"], ...}
```

---

## Testing

```bash
# All tests
python -m pytest tests/ -v

# Specific suite
python -m pytest tests/test_pipeline_integration.py -v
python -m pytest tests/test_consumer_agent.py -v

# With coverage
python -m pytest tests/ --cov=app --cov-report=html

# Regenerate mock fixtures
python -m scripts.generate_mock_data --store-id BHX-HCM001
```

Expected: **96+ tests passing**.

---

## Further Reading

- [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) — Full architecture, algorithm specs, data models, data flow, frontend integration
