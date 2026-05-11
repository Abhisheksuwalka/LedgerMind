# 🧠 LedgerMind

**AI-powered CFO for indie SaaS founders — runs 100% on free LLMs.**

Upload your Stripe CSV or any transaction export → get a CFO-grade report
in under 60 seconds: burn rate, runway, anomaly flags, 90-day projection.

---

## ✨ What It Does

| Step | Agent | Output |
|------|-------|--------|
| 1 | Data Ingestion | Parses CSV/JSON, stores to PostgreSQL |
| 2 | P&L Analyzer | Revenue, expenses, gross margin, net profit |
| 3 | Forecasting | 30/60/90-day cash flow projection |
| 4 | Anomaly Detection | Z-score + IQR outlier detection with LLM explanations |
| 5 | Reconciliation | Period-over-period category variance analysis |
| 6 | Report Generator | Executive Markdown report with narrative |
| 7 | Notification | Email delivery (SendGrid — optional) |
| 8 | Audit | Per-agent token usage and timing logged to DB |
| 9 | Dashboard | Live WebSocket push to React frontend |

---

## 🏗️ Architecture

- **Backend:** FastAPI + LangGraph (async, parallel agent fan-out)
- **Database:** PostgreSQL via SQLAlchemy async + Alembic migrations
- **Queue:** Redis + Celery Beat (nightly scheduled runs)
- **Frontend:** React 18 + TypeScript + Tailwind + Recharts
- **LLM Strategy:** Groq (free primary) → Gemini (free secondary) → Anthropic (paid optional)

### Pipeline Flow

```
Upload CSV
    ↓
POST /api/v1/run → 202 Accepted (non-blocking)
    ↓
Background Task
    ↓
data_ingestion
    ↓ (fan-out)
[pnl_analyzer] [forecasting] [anomaly_detection] [reconciliation]  ← PARALLEL
    ↓ (fan-in)
report_generator → notification → audit → dashboard
    ↓
WebSocket push → React Dashboard
```

---

## 🆓 LLM Cost Strategy

| Agent | Provider | Cost |
|-------|----------|------|
| P&L Analyzer | Groq llama-3.3-70b | Free |
| Forecasting | Groq llama-3.3-70b | Free |
| Anomaly Detection | Groq llama-3.3-70b | Free |
| Reconciliation | Gemini 2.0 Flash | Free |
| Report Generator | Anthropic Sonnet (optional) | ~$0.01/run |

**Total cost per run: $0.00** (with only free providers configured)

---

## 🚀 Quick Start

### 1. Clone and Configure
```bash
git clone <repo>
cd FinAgent-OS
cp .env.example .env
# Add your free API key (get from https://console.groq.com/keys):
# GROQ_API_KEY=gsk_...
```

### 2. Running with Docker (Recommended)
This is the easiest way to start the entire stack (PostgreSQL, Redis, Celery, FastAPI, React).
```bash
docker compose up --build
```

### 3. Open the Dashboard
Once Docker is running, you can access the services:
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 4. Run a Pipeline Manually
```bash
curl -X POST http://localhost:8000/api/v1/run \
  -F "file=@sample_transactions.csv" \
  -F "file_type=csv"
# Returns: {"run_id": "...", "status": "accepted"}
```

### 5. Running the Test Suite
The project includes a robust `pytest` suite testing all core LLM/analysis logic and End-to-End integrations. 

**Terminal 1 (Start the Backend):**
Make sure the Docker stack is running so the integration tests can hit the API:
```bash
docker compose up
```

**Terminal 2 (Run Tests):**
Set up the Python virtual environment and run the tests:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

### CSV Format

```csv
date,description,amount,category
2024-01-15,Monthly SaaS Revenue,12000,revenue
2024-01-15,AWS Infrastructure,-1200,expense
2024-01-16,Staff Salaries,-8500,expense
```

- `amount` — positive = revenue, negative = expense
- `category` — optional (auto-inferred if missing)

---

## 🔑 Getting Free API Keys

| Provider | Link | Free Tier |
|----------|------|-----------|
| Groq | https://console.groq.com/keys | 30 req/min, unlimited/day |
| Gemini | https://aistudio.google.com/apikey | 1500 req/day |
| Anthropic | https://console.anthropic.com | $5 free credit (optional) |

---

## 📂 Project Structure

```
FinAgent-OS-main/
├── backend/
│   ├── agents/           # 10 modular agent files
│   ├── tools/
│   │   ├── llm_router.py # Provider-agnostic LLM abstraction
│   │   └── json_utils.py # Robust JSON extraction
│   ├── ws/manager.py     # WebSocket connection manager
│   ├── graph/workflow.py # LangGraph pipeline (parallel fan-out)
│   ├── api/routes.py     # FastAPI routes (202 non-blocking)
│   ├── db/models.py      # SQLAlchemy async models
│   └── alembic/          # Database migrations
├── frontend/src/
│   ├── pages/            # Dashboard, Reports, Settings
│   ├── components/       # AgentActivityFeed, Charts, etc.
│   └── hooks/            # useWebSocket
├── docker-compose.yml
├── sample_transactions.csv
└── .env.example
```

---

## 🧠 Engineering Choices & Optimizations

### Why LangGraph?
- Enables true parallel agent fan-out (4 agents run concurrently, not sequentially)
- Built-in state management with typed reducers prevents race conditions
- Conditional routing allows skipping agents on failure without crashing the pipeline

### Why `asyncio.create_task` (not Celery for the pipeline)?
- The pipeline uses async SQLAlchemy and async LLM clients — running in asyncio keeps the same event loop
- Celery workers are sync by default; wrapping async code in `asyncio.run()` inside Celery creates a new event loop per task, which leaks async connections
- `create_task` is simpler, faster, and avoids the Celery+asyncio anti-pattern

### Why Groq as primary LLM?
- Free tier with 30 req/min
- `llama-3.3-70b-versatile` is genuinely capable for financial narrative generation
- Response latency ~1–3s vs ~8–15s for Claude Sonnet — makes the pipeline ~4x faster

### How parallel fan-out works
- LangGraph `add_conditional_edges` returns a list of node names → all 4 analysis agents start simultaneously
- `Annotated[list[str], operator.add]` reducers on `completed_agents` and `errors` safely merge parallel state updates
- `route_after_analysis` acts as a fan-in gate: only proceeds to `report_generator` when all 4 are in `completed_agents`

### How to add a new agent
1. Create `backend/agents/my_agent.py` with an `async def run(ingestion_result, run_id) -> dict` function
2. Add `make_my_agent_node()` factory to `workflow.py`
3. Add `graph.add_node()` and appropriate edges in `build_graph()`
4. No other changes needed — state is shared automatically

---

## 📊 Sample Output

After uploading `sample_transactions.csv`:
- Revenue: $147,500 | Expenses: $89,200 | Net Profit: $43,725
- Anomaly flagged: `SUSPICIOUS LARGE PAYMENT -$45,000` (Z-score: 3.8, severity: critical)
- 90-day forecast: Positive cash flow trend, $12,000/month projected
- Report: Full executive Markdown in Reports tab

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/run` | Upload file + trigger full pipeline |
| `GET` | `/api/v1/runs/{run_id}/status` | Poll pipeline run status |
| `GET` | `/api/v1/runs` | List all pipeline runs |
| `GET` | `/api/v1/reports` | List all generated reports |
| `GET` | `/api/v1/reports/{id}` | Get full report with markdown |
| `GET` | `/api/v1/audit/{run_id}` | Get audit trail for a run |
| `GET` | `/api/v1/settings` | Current provider config (read-only) |
| `WS`  | `/ws` | WebSocket — live agent events |
| `GET` | `/health` | Health check |

---

## License

MIT
