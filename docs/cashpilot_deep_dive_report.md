# CashPilot — Deep-Dive Implementation Audit Report

> **Status:** Living document — updated as audit progresses  
> **Date:** May 2026  
> **Scope:** Full-stack audit against `cashpilot_product_plan.md`

---

## Executive Summary

The project is **~55% complete**. The backend is genuinely well-built — the LangGraph pipeline, financial tools, chat agent, database schema, watch engine endpoints, and Celery tasks are all real and substantive. The frontend is where most of the debt lives: the two most important user-facing features (Chat and Snapshot) are connected to **mock data only**, the Alerts and History pages are **not even registered as routes**, and the upload flow **never actually calls the backend API**.

---

## Section 1: Backend Audit

### 1.1 Database Models (`backend/db/models.py`) — ✅ COMPLETE

All five CashPilot tables are defined and correct:
- `PipelineRun` ✅
- `Transaction` ✅ (includes `business_id` FK)
- `AuditLog` ✅
- `FinancialReport` ✅
- `BusinessProfile` ✅ (health_score, avg_monthly stats, upload tracking)
- `CategoryBaseline` ✅ (EWMA + ewmstd + n_observations per month/category)
- `Alert` ✅ (alert_type, severity, is_read)
- `ChatMessage` ✅ (role, tool_calls_json, session_id)

**Issues:**
- `init_db()` uses `subprocess.run(["alembic", "upgrade", "head"])` inside an async context — this blocks the event loop and is fragile in containers. (Minor but real.)

---

### 1.2 API Routes (`backend/api/routes.py`) — ✅ MOSTLY COMPLETE

| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /run` | ✅ Real | Accepts file upload, fires pipeline in background |
| `GET /runs/{id}/status` | ✅ Real | DB polling |
| `GET /runs` | ✅ Real | Lists 50 most recent runs |
| `GET /reports` | ✅ Real | Lists reports |
| `GET /reports/{id}` | ✅ Real | Returns structured JSON |
| `GET /audit/{run_id}` | ✅ Real | Returns audit logs |
| `GET /settings` | ✅ Real | Returns provider config from env vars |
| `POST /chat` | ✅ Real | Full ReAct agent |
| `GET /chat/{session_id}/history` | ✅ Real | Redis-backed |
| `DELETE /chat/{session_id}` | ✅ Real | Clears Redis |
| `GET /alerts` | ✅ Real | DB query |
| `PATCH /alerts/{id}/read` | ✅ Real | Marks as read |
| `POST /internal/nightly-delta` | ✅ Real | Full watch engine logic |
| `POST /internal/weekly-digest` | ✅ Real | LLM-generated summary |
| **MISSING: `GET /snapshot`** | ❌ MISSING | No endpoint serves the dashboard data the frontend needs |
| **MISSING: `GET /history`** | ❌ MISSING | No endpoint for analysis run history |
| **MISSING: `POST /alerts/{id}/dismiss`** | ❌ MISSING | Frontend calls this but it doesn't exist |

**Critical Gap:** There is no `/api/v1/snapshot` endpoint. The frontend Snapshot page needs a single endpoint that returns `{quickStats, chartData, healthScore, anomalies, lastSyncedAt}` — aggregated from the latest pipeline run and business profile. Without this, Snapshot will always show mock data.

---

### 1.3 Financial Tools (`backend/tools/financial_tools.py`) — ✅ COMPLETE

All 6 tools are real and well-implemented:
- `compute_pnl` ✅ — revenue, expenses, gross profit, net profit, margin, category breakdown
- `compute_runway` ✅ — EWMA burn rate, scenario support, warning messages
- `query_transactions` ✅ — aggregation modes (sum/count/avg), group_by (category/month)
- `compare_periods` ✅ — any two periods, any metric
- `find_anomalies` ✅ — EWMA baseline + global Z-score fallback
- `get_category_trends` ✅ — N-month rolling per-category trends

**Minor Issues:**
- `compute_runway` uses net income accumulation as a proxy for cash balance — this is a simplification (real cash balance requires a balance sheet, not just net P&L). Acceptable for MVP but should be documented.
- `find_anomalies` doesn't return a `method_used` field consistently in all paths.

---

### 1.4 Chat Agent (`backend/agents/chat_agent.py`) — ✅ COMPLETE

Real LangGraph ReAct loop:
- Proper `ChatState` TypedDict with message accumulation
- `call_model` → `should_continue` → `tool_node` → `call_model` cycle
- `MAX_TOOL_ITERATIONS = 8` safety cap
- Redis history persistence (24hr TTL, last 20 messages)
- PostgreSQL permanent record via `ChatMessage` model
- Returns `{response, tools_used, session_id, message_count}`

---

### 1.5 Chat Tools (`backend/agents/chat_tools_lc.py`) — ✅ COMPLETE

LangChain `@tool`-decorated wrappers around `financial_tools.py`. These are the tools the LLM agent actually calls.

---

### 1.6 Watch Engine — ✅ COMPLETE (Backend)

- Celery Beat schedules: nightly delta at midnight UTC, weekly digest Monday 8am UTC ✅
- `nightly_delta_check` task → POST to `/internal/nightly-delta` ✅
- `weekly_digest` task → POST to `/internal/weekly-digest` ✅
- Alert creation + WebSocket broadcast ✅

---

### 1.7 Data Ingestion (`backend/agents/data_ingestion.py`) — ✅ MOSTLY COMPLETE

- CSV parsing with Stripe auto-detection ✅
- JSON parsing ✅
- Bulk insert using `db.add_all()` (not `iterrows()`) ✅
- Input validation (size, row count, date range) ✅

**Gap:** 
- **No deduplication** — uploading the same CSV twice creates duplicate transactions. The plan specified SHA-256 hash-based deduplication but it was not implemented.
- **No `business_id` assignment during ingestion** — transactions are inserted without `business_id`, so the financial tools (which filter by `business_id`) can't find them.

---

### 1.8 Services Layer — ✅ COMPLETE

- `baseline_updater.py` — EWMA CategoryBaseline update logic ✅
- `profile_service.py` — get/create single-tenant BusinessProfile ✅

**Gap:** `baseline_updater` is implemented but **never called** after ingestion. The `data_ingestion.py` agent doesn't invoke it, so `CategoryBaseline` is never populated, which means `find_anomalies` always falls back to global Z-score.

---

### 1.9 WebSocket (`backend/ws/manager.py`) — ✅ COMPLETE

Connection manager with broadcast functionality. Properly mounted at `/ws` in `main.py`.

---

## Section 2: Frontend Audit

### 2.1 Router (`frontend/src/App.tsx`) — ❌ INCOMPLETE

```
/ → Snapshot ✅ (route exists, but data is mock)
/chat → Chat ✅ (route exists, but not connected to backend)
/settings → Settings ✅ (route exists, UI is placeholder)
/alerts → COMMENTED OUT ❌
/history → COMMENTED OUT ❌
```

The `Alerts` and `History` routes are explicitly commented out. Clicking them in the sidebar navigates to a non-existent route.

---

### 2.2 Snapshot Page — ❌ MOCK DATA ONLY

**File:** `frontend/src/features/snapshot/hooks/useSnapshotData.ts`

The hook contains hardcoded mock data:
```ts
// Simulate API call delay
await new Promise(resolve => setTimeout(resolve, 800));
return mockSnapshotData;   // <-- Always returns fake data
```

The frontend has all the UI components (QuickStats, RevenueExpenseChart, HealthScoreGauge, AnomalyWidget) but they render **2023 fake data, not your real transactions**.

**What's needed:** Wire `useSnapshotData` to call the real `/api/v1/snapshot` endpoint (which also needs to be created on the backend).

---

### 2.3 Chat Page — ❌ MOCK RESPONSE ONLY

**File:** `frontend/src/features/chat/hooks/useChatSession.ts`

```ts
// Mock API call delay
setTimeout(() => {
  const assistantMessage: Message = {
    content: `I received your message: "${content}". This is a mock response from CashPilot.`,
  };
}, 1500);

// TODO: Wire up real API when backend is ready
/*
  const response = await api.post('/api/v1/chat', { ... });
*/
```

The entire real API call is commented out. The chat UI components are good (MessageBubble, ChatInput, SuggestedPrompts, ToolCallPill), but the backend integration is **zero**.

**Consequence:** Every chat message gets "I received your message: 'X'. This is a mock response from CashPilot." — the ReAct agent that was built is never invoked.

---

### 2.4 Alerts Page — ❌ MOCK DATA + NOT ROUTED

**File:** `frontend/src/features/alerts/hooks/useAlerts.ts`

The hook uses a hardcoded `MOCK_ALERTS` array (9 alerts about CPU usage, database connections, server issues — generic infrastructure alerts unrelated to finance).

The mutations (mark read, dismiss) work in-memory but **never call the backend**.

The route `/alerts` is commented out in `App.tsx` so clicking Alerts in the sidebar navigates to 404→redirect.

---

### 2.5 History Page — ❌ COMPLETELY MISSING

The route is commented out. The `features/history` directory exists but contains no implementation.

**What's needed:** A page that lists past pipeline runs (from `/api/v1/runs`) with their status and links to view the report.

---

### 2.6 Settings Page — ⚠️ PARTIAL

There are **two** Settings components:
- `frontend/src/pages/Settings.tsx` — The old version, **imports from wrong path**, not connected to the router (which uses `features/settings/Settings.tsx`).
- `frontend/src/features/settings/Settings.tsx` — The current version, renders `ProfileForm`, `BusinessProfileForm`, `IntegrationCard`, `NotificationToggles`.

**Issues with `features/settings/Settings.tsx`:**
- `stripeConnected` and `plaidConnected` are local state — connecting/disconnecting doesn't call any API.
- Integration cards are purely cosmetic.
- No link to the actual `/api/v1/settings` endpoint — provider status is not displayed.
- Stripe integration is shown as "connected" by default (`useState(true)`) — this is misleading.

---

### 2.7 Upload Modal (`frontend/src/components/modals/UploadModal.tsx`) — ❌ FAKE UPLOAD

The upload modal has excellent UI (drag-and-drop, progress bar, analysis steps animation) but:

```ts
const startUpload = (selectedFile: File) => {
  setFile(selectedFile);
  setUploadState('uploading');
  setProgress(0);
  // <-- No actual API call here
};
```

The `uploading` state is driven by a fake `setInterval` that increments progress to 100%, then simulates "analyzing" steps, then auto-closes the modal after 5.5 seconds. **The file is never sent to the backend.**

**Also missing:** No CSV file format guide or example file download link for users who don't know the expected format.

---

### 2.8 WebSocket Connection — ⚠️ CONNECTED BUT LIMITED

`useWebSocket` properly connects to `ws://localhost:8000/ws` and handles `alert`, `analysis_progress`, and `chat_tool_call` message types.

**Issues:**
- No reconnect logic — if the WebSocket drops, it stays disconnected silently.
- `alert` events increment the unread counter but don't inject the alert into the Alerts list (which uses mock data anyway).
- `analysis_progress` logs to console but shows no UI feedback (no toast, no progress indicator).

---

### 2.9 API Client — ❌ MISSING

There is no centralized API client module (`frontend/src/lib/api.ts` doesn't exist). Each component that does fetch the API (only `pages/Settings.tsx` actually does) uses raw `fetch()` with hardcoded URLs.

**Consequence:** No centralized error handling, no auth header injection, no base URL management.

---

### 2.10 Sidebar Navigation — ⚠️ MISLEADING

The Sidebar lists 5 nav items including Alerts and History, but these routes don't exist. Clicking them silently redirects to `/` (Snapshot). The user has no idea the pages don't work.

---

## Section 3: Feature-by-Feature Gap Matrix

| Feature | Planned | Backend | Frontend | End-to-End |
|---------|---------|---------|----------|------------|
| CSV Upload & Pipeline | ✅ | ✅ Real | ❌ Fake/no call | ❌ |
| Financial Snapshot Dashboard | ✅ | ❌ No endpoint | ❌ Mock data | ❌ |
| Chat with CashPilot | ✅ | ✅ Real ReAct agent | ❌ Mock response | ❌ |
| Alert Feed | ✅ | ✅ Real alerts | ❌ Mock data, not routed | ❌ |
| Analysis History | ✅ | ✅ `/runs` endpoint | ❌ Missing page | ❌ |
| Watch Engine (Celery) | ✅ | ✅ Real tasks | N/A | ✅ |
| WebSocket Alerts | ✅ | ✅ Real broadcast | ⚠️ Connected, no UI | ⚠️ |
| Settings/Provider Status | ✅ | ✅ `/settings` endpoint | ⚠️ Not wired | ⚠️ |
| Business Profile | ✅ | ✅ Model + service | ❌ Not displayed | ❌ |
| Runway Calculator | ✅ | ✅ Tool exists | ❌ Not shown on dashboard | ❌ |
| Category Baselines (EWMA) | ✅ | ✅ Model + service | N/A | ❌ (never called) |
| Deduplication (SHA-256) | ✅ | ❌ Missing | ❌ | ❌ |
| business_id on transactions | ✅ | ❌ Not set in ingestion | ❌ | ❌ |

---

## Section 4: Critical Bugs That Must Be Fixed First

### Bug 1: Transactions Have No `business_id`
`data_ingestion.py` creates `Transaction` objects without setting `business_id`. Every financial tool filters by `business_id`, so they return empty results. This is the most critical bug — **nothing works** without fixing it.

### Bug 2: `baseline_updater` Never Called
`services/baseline_updater.py` exists but is never invoked after ingestion. CategoryBaseline is always empty, so anomaly detection always falls back to global Z-score.

### Bug 3: Chat Frontend Is Mock
`useChatSession.ts` has the real API call commented out. The ReAct agent on the backend is never used.

### Bug 4: Upload Modal Doesn't Upload
`UploadModal.tsx` fakes the upload with a timer. Nothing reaches the backend.

### Bug 5: Alerts and History Are Not Routed
Both routes are commented out in `App.tsx`.

### Bug 6: No `/api/v1/snapshot` Endpoint
The Snapshot page has no real data source.

### Bug 7: Alert Dismiss API Doesn't Exist
Frontend calls dismiss but the backend has no `DELETE /alerts/{id}` or equivalent.

---

## Section 5: Missing Features from the Product Plan

1. **CSV format guide** — the plan specifies users need to know the expected CSV format on first use. No help text exists.
2. **Stripe webhook endpoint** (`POST /api/v1/webhooks/stripe`) — planned for Week 4, not implemented.
3. **Onboarding flow** — "upload → snapshot → chat prompt" sequence. The first-time experience is not guided.
4. **Chat streaming** — the plan specifies typed streaming responses. Currently request/response only.
5. **Tool call display in chat** — `ToolCallPill` component exists but is not rendered because `tools_used` is never returned (mock response has no tools).
6. **Anomaly → Chat link** — "Ask me about this" button on anomaly items was planned.
7. **Runway indicator on dashboard** — the most important KPI is not a QuickStat card.
8. **Period selector on Snapshot** — `useSnapshotData` accepts a `timeRange` param but UI has no control.

---

*Last updated: May 2026*
