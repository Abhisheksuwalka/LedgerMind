# Changelog

All notable changes to LedgerMind are documented here.

---

## [2.0.0] — 2026-05-11 — LedgerMind (Phase 2)

### 🚀 Breaking Changes
- App renamed from **FinAgent OS** → **LedgerMind** across all surfaces (titles, health endpoint, email subjects, README, API docstrings)
- `AuditLog.claude_model` DB column renamed to `llm_provider` (migration `120b28443fb2`)

### ✨ New Features

#### Provider-Agnostic LLM Router (`backend/tools/llm_router.py`)
- 4-provider chain: **Groq → Gemini → Anthropic → Ollama**
- Only includes providers whose API key is set in `.env`
- Explicit `RuntimeError` if no provider configured (no silent crash)
- `prefer_provider` parameter lets report generator request Anthropic while falling back gracefully
- Redis caching shared with all agents
- Startup diagnostic log: `[LLMRouter] Provider status: ✓ groq, ✗ anthropic`

#### All 5 LLM Agents Migrated
- `pnl_analyzer`, `forecasting`, `anomaly_detection`, `reconciliation`, `report_generator` all import `run_agent` from `tools.llm_router` — zero dependency on Anthropic key
- Removed `SONNET` constant from all agent files

#### Free-Tier by Default
- App runs end-to-end with **only `GROQ_API_KEY`** (free from console.groq.com)
- Groq llama-3.3-70b: ~1–3s latency vs ~8–15s for Claude

#### Settings Page — Live Provider Status
- `Settings.tsx` now fetches `GET /api/v1/settings` and shows real-time green/red provider badges
- Removed all hardcoded `claude-sonnet-4-6` / `claude-opus-4-6` references

#### Reports Page — Markdown Rendering
- `Reports.tsx` renders `markdown_report` as formatted HTML (headings, bold, lists, code, `<hr>`)
- Replaced raw `<pre>` tag with styled prose view

#### Reconciliation — Period-Over-Period Variance
- Replaced broken even-count "matched" heuristic with real period-over-period category variance
- Splits transactions into two date-halves; flags categories with >20% spend change
- LLM now receives meaningful variance data with actual `pct_change` values per category

#### WebSocket Manager Extracted
- `ConnectionManager` moved from `main.py` → `backend/ws/manager.py`
- Adds dead-connection pruning log and safe membership check before remove

#### Celery Anti-Pattern Fixed
- Replaced `asyncio.run(_async_scheduled_run())` inside Celery worker with a sync HTTP POST to `/api/v1/run`
- Avoids event loop leaks from `asyncio.run()` inside Celery's sync context

### 🔧 Configuration

#### `.env.example` Rewritten
- Documents all 4 LLM providers with get-key links
- `GROQ_MODEL`, `GEMINI_MODEL`, `ANTHROPIC_MODEL` overrides
- `TAX_RATE_PCT` documented
- `NOTIFICATION_EMAIL` replaces `ALERT_EMAIL_RECIPIENT`

### 🗑️ Removed
- `backend/tools/claude_client.py` — superseded by `llm_router.py`
- `scikit-learn` from requirements (unused)
- `i.py` scratch file

### 🐛 Bug Fixes
- `audit.py`: `claude_model=` kwarg renamed to `llm_provider=` to match DB column
- `celery_tasks/tasks.py`: `datetime.utcnow()` in completed_at → `datetime.now(timezone.utc)` (timezone-aware)
- `anomaly_detection.py`: Missing `except` block (syntax error) fixed
- `Dashboard.tsx`: `useState` → `useEffect` import bug fixed

---

## [1.0.0] — Initial Release — FinAgent OS (Phase 1)

- 10-agent LangGraph pipeline (orchestrator, ingestion, P&L, forecasting, anomaly, reconciliation, report, notification, audit, dashboard)
- True parallel fan-out: 4 analysis agents run concurrently via LangGraph conditional edges
- `operator.add` reducers for safe parallel state merges
- `POST /run` returns 202 immediately; pipeline runs via `asyncio.create_task`
- `GET /runs/{run_id}/status` polling endpoint
- `GET /api/v1/settings` read-only config endpoint
- WebSocket live agent events (`agent_started`, `agent_done`, `agent_error`)
- Redis caching for LLM responses (1-hour TTL)
- Alembic migrations with timezone-aware `DateTime(timezone=True)` columns
- `json_utils.py` — robust JSON extraction from LLM responses (3 fallback strategies)
- `sample_transactions.csv` for quick demo runs
- Input validation in data_ingestion: file size (10 MB), row count, date parsing
