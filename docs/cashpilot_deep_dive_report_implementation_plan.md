# CashPilot — Fix Everything Implementation Plan

> **Goal:** Transform the project from ~55% complete to a fully working end-to-end product.  
> **Approach:** Fix backend bugs first (data integrity), then add missing endpoints, then wire the frontend, then add missing pages.

---

## Phase 1 — Backend Critical Bug Fixes (Must Do First)

These bugs make everything else non-functional. Nothing works until these are fixed.

### 1A. Fix `business_id` assignment during ingestion
#### [MODIFY] [data_ingestion.py](file:///Users/abhisheksuwalka/SEM-8/mini-projects/finance%20agentic%20ai%20project/FinAgent-OS-main/backend/agents/data_ingestion.py)
- `ingest()` must accept a `business_id: Optional[UUID]` parameter
- Set `business_id=business_id` on each `Transaction` object before `db.add_all()`
- After inserting transactions, call `baseline_updater.update_baselines_from_transactions(db, business_id, tx_objects)`

#### [MODIFY] [graph/workflow.py]
- Pass `business_id` from the BusinessProfile into the ingestion node

### 1B. Wire `baseline_updater` after ingestion
#### [MODIFY] [agents/data_ingestion.py]
- Import and call `update_baselines_from_transactions` after the bulk insert and commit

### 1C. Add SHA-256 deduplication
#### [MODIFY] [agents/data_ingestion.py]
- Compute SHA-256 of the file content before parsing
- Store the hash on `PipelineRun` (add `data_hash` column)
- Before ingestion, check if a run with the same hash exists → return early with `"status": "duplicate"`

#### [NEW] Alembic migration for `data_hash` column on `pipeline_runs`

### 1D. Fix `alert dismiss` endpoint
#### [MODIFY] [api/routes.py]
- Add `DELETE /alerts/{alert_id}` endpoint that deletes the alert record

---

## Phase 2 — Missing Backend Endpoints

### 2A. Add `/api/v1/snapshot` endpoint
#### [MODIFY] [api/routes.py]
This is the single most important missing endpoint. It must return:
```json
{
  "quickStats": {
    "totalRevenue": { "value": 0, "trend": 0, "trendDirection": "neutral", "sparkline": [] },
    "totalExpenses": { "value": 0, "trend": 0, "trendDirection": "neutral", "sparkline": [] },
    "netProfitMargin": { "value": 0, "trend": 0, "trendDirection": "neutral", "sparkline": [] },
    "cashRunway": { "value": 0, "trend": 0, "trendDirection": "neutral", "sparkline": [] }
  },
  "chartData": [{ "date": "...", "revenue": 0, "expenses": 0 }],
  "healthScore": 50,
  "anomalies": [{ "id": "...", "title": "...", "severity": "...", "date": "...", "amount": 0 }],
  "lastSyncedAt": "..."
}
```

Implementation:
- `GET /api/v1/snapshot` — queries the latest BusinessProfile, runs `compute_pnl` for this month vs last month, calls `compute_runway`, calls `find_anomalies`, assembles the response.
- Optional `?period=3M|6M|12M` param for chart data range

### 2B. Add `/api/v1/history` endpoint
#### [MODIFY] [api/routes.py]
- `GET /api/v1/history` — returns list of pipeline runs with their associated reports and status
- Each item: `{run_id, status, started_at, completed_at, report_summary, transaction_count}`

### 2C. Fix Alert dismiss
Already covered in Phase 1D.

---

## Phase 3 — Frontend API Wiring

### 3A. Create centralized API client
#### [NEW] [frontend/src/lib/api.ts]
```ts
const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api/v1${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options?.headers,
    },
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json();
}
```

### 3B. Wire Snapshot to real backend
#### [MODIFY] [frontend/src/features/snapshot/hooks/useSnapshotData.ts]
- Replace mock data with `apiFetch<SnapshotData>('/snapshot')`
- Keep mock as fallback for dev when backend is down (env-gated)

### 3C. Wire Chat to real backend  
#### [MODIFY] [frontend/src/features/chat/hooks/useChatSession.ts]
- Uncomment the real API call
- Use `apiFetch('/chat', { method: 'POST', body: JSON.stringify({session_id, message}) })`
- Parse `response`, `tools_used` from the response
- Display `tools_used` in `ToolCallPill` if non-empty
- Implement abort controller for the "Stop" button

### 3D. Wire Alerts to real backend
#### [MODIFY] [frontend/src/features/alerts/hooks/useAlerts.ts]
- Replace `MOCK_ALERTS` with `apiFetch<Alert[]>('/alerts')`
- Wire `useMarkAlertRead` → `PATCH /alerts/{id}/read`
- Wire `useDismissAlert` → `DELETE /alerts/{id}`
- Wire `useMarkAllRead` → call mark-read for all unread in parallel

### 3E. Wire Upload Modal to real backend
#### [MODIFY] [frontend/src/components/modals/UploadModal.tsx]
- In `startUpload()`, create a `FormData` with the file and post to `POST /api/v1/run`
- Use real `XMLHttpRequest` (for upload progress events) or `fetch`
- On response, save the `run_id` to AppContext
- Poll `GET /runs/{run_id}/status` every 2 seconds, updating the analysis steps
- On completion, invalidate the snapshot query so the dashboard refreshes
- Accept both CSV files (existing) — **no change needed to acceptance** since backend already accepts CSV

### 3F. Wire Settings to real backend
#### [MODIFY] [frontend/src/features/settings/Settings.tsx]
- Fetch from `GET /api/v1/settings` and display provider status
- Remove hardcoded `stripeConnected = true` default

### 3G. WebSocket reconnect + alert injection
#### [MODIFY] [frontend/src/hooks/useWebSocket.ts]
- Add exponential backoff reconnect (max 30s)
- On `alert` event: invalidate `['alerts']` React Query cache (not just increment counter)

---

## Phase 4 — Missing Pages & Navigation

### 4A. Add Alerts page to router
#### [MODIFY] [frontend/src/App.tsx]
- Uncomment `<Route path="alerts" element={<Alerts />} />`
- Import `Alerts` from `features/alerts/Alerts.tsx`

### 4B. Create History page
#### [NEW] [frontend/src/features/history/History.tsx]
```tsx
// Fetches from GET /api/v1/history
// Shows a timeline of pipeline runs with status badges
// Clicking a run shows the report details
```

#### [NEW] [frontend/src/features/history/hooks/useHistory.ts]
- `useQuery` to fetch `/history`

#### [MODIFY] [frontend/src/App.tsx]
- Add `<Route path="history" element={<History />} />`

### 4C. Fix Sidebar navigation (remove dead links)
The Sidebar already has all 5 nav items. Once routes are added, they'll work automatically.

---

## Phase 5 — Product-Level Polish

### 5A. Add Runway card to Snapshot QuickStats
#### [MODIFY] [backend/api/routes.py (snapshot endpoint)]
- Ensure `cashRunway` field is populated from `compute_runway()`

#### [MODIFY] [frontend/src/features/snapshot/components/QuickStats.tsx]
- Render RunwayBar component for cashRunway stat

### 5B. Add "Ask me about this" button on Anomaly items
#### [MODIFY] [frontend/src/features/snapshot/components/AnomalyWidget.tsx]
- Add a button that navigates to `/chat` with a pre-filled question about the anomaly
- Use `useNavigate` from react-router-dom with state

### 5C. Add period selector to Snapshot
#### [MODIFY] [frontend/src/features/snapshot/Snapshot.tsx]
- Add `<select>` or button group: 3M | 6M | 12M
- Pass selected value to `useSnapshotData(period)`

### 5D. CSV format guide in Upload Modal
#### [MODIFY] [frontend/src/components/modals/UploadModal.tsx]
- Add a collapsible "Expected format" section showing required columns: `date, description, amount`
- Add a "Download sample CSV" link pointing to the `sample_transactions.csv` file

### 5E. Remove duplicate `pages/Settings.tsx`
#### [DELETE] [frontend/src/pages/Settings.tsx]
- This old file is not used (router points to `features/settings/Settings.tsx`)

---

## Verification Plan

### After Phase 1 (Backend Bugs):
- Run pipeline with `sample_transactions.csv`
- Query `SELECT * FROM transactions WHERE business_id IS NOT NULL` — should have rows
- Query `SELECT * FROM category_baselines` — should have rows after ingestion

### After Phase 2 (Missing Endpoints):
- `curl http://localhost:8000/api/v1/snapshot` — should return real data
- `curl http://localhost:8000/api/v1/history` — should return run list

### After Phase 3 (Frontend Wiring):
- Upload the sample CSV → see real progress → Snapshot refreshes with real numbers
- Send a chat message → get a real agent response with tools_used
- Alerts page loads real alerts from DB

### After Phase 4 (Navigation):
- All 5 sidebar links navigate correctly
- History page shows pipeline runs

### After Phase 5 (Polish):
- First-time experience: upload → snapshot with data → chat prompt
- Runway is visible on dashboard
- Anomaly "ask me" button pre-fills chat

---

## Priority Order (What to Fix First)

1. **Bug 1A** — `business_id` on transactions ← everything depends on this
2. **Bug 3E** — Upload Modal actually uploads ← users can't add data otherwise  
3. **2A** — `/snapshot` endpoint ← dashboard needs data
4. **3B** — Snapshot frontend wired ← dashboard shows real data
5. **3C** — Chat frontend wired ← the killer feature works
6. **4A** — Alerts routed ← dead nav link fixed
7. **3D** — Alerts wired to backend ← real alerts displayed
8. **4B** — History page ← complete navigation
9. **1B** — baseline_updater called ← smarter anomaly detection
10. All Phase 5 items — product polish

