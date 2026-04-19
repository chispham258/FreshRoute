# FreshRoute

AI-powered food waste reduction for Vietnamese retail. Two agents, one pipeline.

- **B2B agent** — recommends discounted recipe bundles to stores using expiring inventory
- **Consumer agent** — helps home cooks find recipes from what they have and builds a shopping list

Built at GDSC Hackathon 2026 · Team FreshRoute

---

## Architecture

```
Admin Portal / Customer Portal / AI Chat
              │
         FastAPI (app/main.py)
         /            \
    B2B Agent      Consumer Agent        ← LangGraph StateGraph
        \               /
    Deterministic Pipeline (P1→P7)       ← fallback / finalization
              │
         DataRepository                  ← 93 SKUs · 40 recipes · singleton
```

Both agents are custom LangGraph `StateGraph`s with explicit routing and a `_recover_tool_call_from_text` fallback (the FPT AI Factory model returns tool calls as plain text — AST parsing reconstructs proper `AIMessage`s).

---

## Quick Start

**Requirements:** Python 3.13+, [uv](https://docs.astral.sh/uv/), Node.js 18+, FPT AI Factory API key

```bash
# Backend
uv sync
cp .env.example .env   # set OPENAI_API_KEY=<fpt-key>
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Docker (all-in-one)
docker-compose up

# Tests
python -m pytest tests/ -v

# Scripts (optional — data generation, seeding)
python -m scripts.generate_mock_data        # Generate test inventory + bundles
python -m scripts.build_inverted_index      # Rebuild recipe search index
python -m scripts.build_mock_user_inventory # Create mock user pantry
python -m scripts.seed_db                   # Seed PostgreSQL (if using postgres connector)
```

Swagger: `http://localhost:8000/docs` · App: `http://localhost:3000`

---

## API

### B2B / Admin

```
GET  /api/admin/combos?storeId=BHX-HCM001     # AI bundle recommendations
GET  /api/admin/inventory?storeId=BHX-HCM001  # near-expiry inventory (P1 scores)
POST /api/admin/combos/{id}/accept
POST /api/admin/combos/{id}/reject
```

### Consumer

```
POST /consumer/chat      # { message, thread_id, allergies? } → { reply, shopping_list?, recipe_suggestions? }
POST /consumer/suggest   # { ingredients: [...], top_k: 3 }
GET  /consumer/api/customer/combos?storeId=BHX-HCM001
```

### Direct Pipeline (no LLM)

```
GET /bundles/BHX-HCM001             # deterministic
GET /bundles/BHX-HCM001?agent=true  # B2B agent path
```

---

## Pipeline (P1→P7)

| Stage | Purpose | Key formula |
| ----- | ------- | ----------- |
| P1 Priority | Expiry risk score per batch | `w_e·exp(-λ·days) + w_s·sigmoid(supply_ratio) + w_d·(1−sell_through)` |
| P2 Retrieval | Match urgent ingredients → recipe candidates | `score = max_urgency + 0.3·Σ(others)` |
| P3 Feasibility | FEFO allocation + substitution | `allocate_fefo()`, completeness ≥ 0.7 |
| P5 Waste | Rescued inventory value | `Σ(priority · cost_per_g · qty_taken_g)` |
| P6 Ranking | Multi-objective score | `w1·urgency + w2·completeness + w3·waste − penalties` |
| P7 Pricing | Dynamic discount | `discount = min(0.05 + 0.25·waste_norm, 0.30)`, margin-floor enforced |

**FEFO strategies:** `strict` (guarantee coverage) · `approx` (minimize waste) · `best` (strict first, fallback to approx if deviation > 25%)

---

## Project Structure

```
app/
├── agent/
│   ├── b2b/         graph.py · tools.py · prompt.py
│   ├── consumer/    graph.py · tools.py · prompt.py · state.py
│   ├── shared/      tool_factory.py · ontology.py
│   └── tools.py     shared tool implementations
├── core/
│   ├── pipeline/    p1–p7 · orchestrator
│   ├── engine/      allocation.py · waste.py
│   ├── data/        repository.py · skus.py · recipes.py · *.json
│   └── models/      bundle · inventory · recipe
├── api/             bundles · admin · consumer · health
├── integrations/    llm.py (FPTChatOpenAI) · connectors/ · db/
└── main.py

frontend/src/
├── app/
│   ├── admin/page.js
│   └── customer/  page.js · cart/ · ai-chat/
└── lib/  adminApi · customerApi · cart · currency
```

---

## Environment Variables

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `OPENAI_API_KEY` | required | FPT AI Factory key |
| `OPENAI_MODEL` | `gpt-oss-120b` | LLM model ID |
| `TEMPERATURE` | `0.1` | Sampling temperature |
| `DEFAULT_CONNECTOR` | `mock` | `mock` (fixtures) or `postgres` |

---

## Data

- 93 SKUs — fresh meat, seafood, produce, dairy, condiments, dry goods
- 40 Vietnamese recipes
- 178 ingredient aliases for Vietnamese name resolution
- 29 substitution groups in ontology
- 5 urgency decay categories (λ: 0.08 processed → 0.60 fresh seafood)
