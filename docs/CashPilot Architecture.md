# INGEST
**Data ingest layer**
* **CSV / spreadsheet**
  * Stripe, bank, QuickBooks
* **Stripe webhook**
  * Real-time payment events
* **Normalizer**
  * Schema: date, amount, category
* **Dedup**
  * SHA-256 hash

# MEMORY
**Business profile engine — the memory**
* **Transactions**
  * PostgreSQL
  * All normalised rows
* **Category baselines**
  * EWMA per category
  * + month. Updated
  * after every upload
* **Business profile**
  * Revenue / burn stats
  * Health score history
* **Alert log**
  * Type, severity
  * Read / unread

# AGENTS
**Agent layer**
* **Analysis agent**
  * LangGraph ReAct loop
  * compute_pnl
  * find_anomalies
  * compute_runway
  * adapts depth to findings
* **Watch engine**
  * Celery Beat — always on
  * nightly delta check
  * runway threshold alert
  * category spike detector
  * weekly digest email
* **Chat agent**
  * ReAct + tools + memory
  * query_transactions
  * compare_periods
  * compute_runway
  * Redis conversation memory

# LLM router
* Groq (primary, free) -> Gemini (fallback) -> Anthropic (optional quality) -> synthetic (never crashes)

# FRONTEND
**Frontend (React + Vite + Tailwind)**
* **Financial snapshot**
  * Live P&L + health score
  * Runway indicator
  * Multi-run history chart
  * Anomaly feed
* **Chat interface**
  * Ask anything in plain English. Streaming
  * responses. Shows
  * tools used
* **Alert feed**
  * Real-time via WebSocket
  * Severity badges
  * Link to chat for
  * each alert
* **History**
  * All runs
  * compared
  * over time