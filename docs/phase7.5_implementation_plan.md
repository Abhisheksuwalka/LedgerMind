# Goal
Implement Phase 5 of the CashPilot frontend as defined in the PRD. This phase focuses on building the **Alerts** and **History** pages. The Alerts page will display system alerts with filtering and unread states. The History page will display a Health Score History chart and a Data Runs Table with pagination.

## User Review Required
- Please review the sequence of tasks.
- For the `HealthScoreHistory` chart, do we have mock data available or should I generate a mock dataset?
- For the `DataRunsTable`, the PRD mentions pagination. I will implement a local pagination state with mock data for now. Let me know if you want server-side pagination integrated directly.

## Open Questions
- Is `lucide-react` already providing all necessary icons (`Check`, `X`, `MessageSquare`, `Download`)? (Assuming yes, as it's standard).
- I will reuse the `AlertBadge` defined in `Snapshot` if it exists. If not, I'll create it as a shared UI component.

## Proposed Changes

### 1. Types & Schema
#### [NEW] `src/types/alert.ts`
- Define `Alert` interface (id, title, description, severity, createdAt, isRead).
#### [NEW] `src/types/report.ts`
- Define `DataRun` interface for the History table.

### 2. State Management & Hooks (Alerts)
#### [NEW] `src/features/alerts/hooks/useAlerts.ts`
- Implement React Query hooks: `useAlerts`, `useMarkAlertRead`, `useDismissAlert`, `useMarkAllRead`.
- Use mock API calls if the real backend isn't ready.

### 3. Alerts Feature Components
#### [NEW] `src/features/alerts/components/AlertFilters.tsx`
- Severity and Sort order dropdowns using Radix Select.
#### [NEW] `src/features/alerts/components/AlertItem.tsx`
- Layout with SeverityIcon, Title, Description, and action buttons.
- Hover states and dismiss animation.
#### [NEW] `src/features/alerts/components/AlertList.tsx`
- Renders the list of `AlertItem`s.
#### [NEW] `src/features/alerts/Alerts.tsx`
- Main page composition: Page Header, Filter Row, Alert List.

### 4. History Feature Components
#### [NEW] `src/features/history/hooks/useHistory.ts`
- Hooks for fetching chart data and data runs.
#### [NEW] `src/features/history/components/HealthScoreHistory.tsx`
- Full-width area chart using Recharts to plot Health Score over time.
#### [NEW] `src/features/history/components/DataRunsTable.tsx`
- Paginated table showing data processing runs with statuses.
#### [NEW] `src/features/history/History.tsx`
- Main page composition: Page Header, Chart, Table.

### 5. Routing Integration
#### [MODIFY] `src/App.tsx`
- Add routes for `/alerts` and `/history`.

## Verification Plan
### Manual Verification
- Test alert filtering by severity and sorting.
- Test marking alerts as read (UI updates immediately, unread dot disappears).
- Test dismissing alerts (smooth animation).
- Test history chart rendering.
- Test table pagination.
