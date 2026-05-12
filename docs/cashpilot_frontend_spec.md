# CashPilot (LedgerMind) Exhaustive Frontend Architecture & UI Specification

This document provides a highly granular, element-by-element blueprint for the **CashPilot** frontend. It is designed to be ingested by advanced frontend AI tools to orchestrate the exact component structure, UI/UX blocks, and technical implementation.

---

## 1. Project Overview & Context
**CashPilot** (formerly LedgerMind) is an intelligent financial co-pilot for small businesses. It ingests financial data, runs autonomous agentic analysis (via a ReAct LangGraph agent), monitors for anomalies via background tasks (Watch Engine), and provides real-time alerts and interactive chat capabilities.

### 1.1 Technical Stack (Already Initialized)
*   **Core:** React 18, TypeScript, Vite
*   **Styling:** Tailwind CSS (v3.4), `clsx`, `tailwind-merge`, `class-variance-authority` (CVA).
*   **UI Primitives:** Radix UI (`@radix-ui/react-tabs`, `@radix-ui/react-dialog`)
*   **Data Visualization:** Recharts
*   **Icons:** Lucide React
*   **Markdown Rendering:** `react-markdown` (with `@tailwindcss/typography` plugin)
*   **Communication:** REST (Fetch API) & WebSockets for real-time updates.

### 1.2 UI/UX Design Language
*   **Theme:** Modern, professional SaaS dashboard. Needs a clean, high-contrast UI (e.g., slate/gray backgrounds with vibrant primary accents).
*   **Data Density:** High but readable. Use whitespace effectively to separate complex financial metrics.
*   **Visual Indicators:**
    *   **Health/Severity Colors:** Green (Good / > 70 / Low Risk), Yellow/Orange (Warning / 40-70 / Medium Risk), Red (Critical / < 40 / High Risk).
    *   **Trends:** Clear ↑ / ↓ indicators with color coding for positive/negative financial impact.

---

## 2. Global Layout & Application Shell Blocks

The application shell wraps every page and provides global navigation and actions.

### 2.1 Sidebar Navigation Block (Desktop)
*   **Brand Header Element:** "💰 CashPilot" text (bold, modern typography) and logo.
*   **Primary Navigation Menu:**
    *   `Snapshot` (Home Icon) - Default Dashboard.
    *   `Chat` (Message Square Icon) - AI Co-pilot.
    *   `Alerts` (Bell Icon) - Includes dynamic **Unread Badge** (e.g., a red circle with "3").
    *   `History` (Bar Chart Icon) - Historical reports.
    *   `Settings` (Settings/Cog Icon) - Configuration.
*   **User Profile Snippet Element (Bottom):** User Avatar, Name, Email, and current Plan/Tier.
*   **Theme Toggle Element:** Light/Dark mode switcher.

### 2.2 Topbar Block (Mobile & Tablet)
*   **Hamburger Menu Button:** To open a slide-out drawer containing the Sidebar navigation.
*   **Global "Upload Data" Action Button:** Persistent CTA that opens the Data Upload Modal.

### 2.3 Global "Data Upload" Modal Block
*   **Drag & Drop Zone Element:** Dashed border area accepting `.csv` files.
*   **File Status Element:** Shows filename and file size once selected.
*   **Upload Progress Bar Element:** Visual feedback during the upload process.
*   **Analysis Status Indicator Element:** (Post-upload) A spinner or step-tracker showing "CashPilot is analyzing your data...".

---

## 3. Exhaustive Page & Component Breakdown

### 3.1 Snapshot (Dashboard View)
The executive summary view providing immediate insight into business health.

*   **Page Header Block:**
    *   Title: "Financial Snapshot"
    *   Subtitle: "Last synced: [Timestamp]"
    *   Action Element: "Refresh Data" icon button.
*   **KPI Summary Grid Block (Top Row):** Contains 4 independent cards.
    *   **Total Revenue Card:** Big number, micro-sparkline chart (Recharts `TinyLineChart`), and MoM % change badge (e.g., `+12%` in green).
    *   **Total Expenses Card:** Big number, micro-sparkline, and MoM % change badge.
    *   **Net Profit Margin Card:** Percentage value and trend arrow.
    *   **Cash Runway Card:** Value in months (e.g., "6.5 Months"). Includes a horizontal progress bar divided into safe (green) and danger (red) zones based on runway length.
*   **Primary Chart Block (Multi-run P&L):**
    *   **Time Period Toggles:** Buttons for `1M`, `3M`, `6M`, `YTD`, `All`.
    *   **Visualization Element:** Stacked Area Chart or Line Chart (via Recharts) overlaying Revenue vs. Expenses over time.
    *   **Tooltip Element:** Hovering over the chart must show exact date, revenue, and expense numbers.
*   **Health Status Block:**
    *   **Circular Gauge Element (Donut Chart):** Displays a score from 0-100.
    *   **Status Label:** Text dynamically updating based on score (e.g., "Healthy", "Needs Attention").
*   **Live Anomaly Feed Widget Block:**
    *   **Widget Header:** "Recent Anomalies".
    *   **List Items (3-5 max):** Each item contains an Icon (warning), Title, Date, and Severity Pill.
    *   **Action Element:** A small "Ask CashPilot" button on each row that redirects to the Chat tab, pre-filling the input with context.

### 3.2 Chat (AI Co-pilot View)
The conversational interface for interacting with the ReAct analysis agent.

*   **Page Header Block:** "Chat with CashPilot", plus a "Clear Session" button (trash icon).
*   **Empty State Block (When no messages exist):**
    *   **Welcome Banner:** "How can I help you analyze your finances today?"
    *   **Suggested Prompts Element:** 3 clickable pill cards (e.g., "What is my current runway?", "Are there any anomalies this month?", "Show me my revenue trend"). Clicking these auto-sends the message.
*   **Message Feed Block:**
    *   **User Message Bubble:** Right-aligned, primary color background, accompanied by user avatar.
    *   **Agent Message Bubble:** Left-aligned, gray/neutral background, accompanied by CashPilot avatar.
    *   **Rich Text Renderer Element:** Must process Markdown within agent replies (handling `**bold**`, bulleted lists, and rendering raw HTML/Markdown `<table>` into styled Tailwind tables).
    *   **Tool Execution Pill/Badge:** While waiting or within history, show tools used (e.g., "🔧 Running `compute_runway`...").
    *   **Typing Indicator:** A pulsating 3-dot animation when awaiting the LLM response.
*   **Input Area Block:**
    *   **Expanding Textarea Element:** Auto-grows vertically as the user types long queries.
    *   **Send Button Element:** An arrow/plane icon. Turns into a "Stop" (square) icon if response is streaming.
    *   **Session State:** Must save `session_id` locally to preserve the chat on page reload.

### 3.3 Alerts Feed View
A dedicated page for output from the background "Watch Engine".

*   **Page Header Block:** "System Alerts" and a "Mark all as read" ghost button.
*   **Filter & Sort Block:**
    *   **Severity Dropdown:** Filter by `All`, `Critical`, `Warning`, `Info`.
    *   **Sort Dropdown:** `Newest First`, `Oldest First`.
*   **Alert List Block:**
    *   **Unread Alert Item Element:** Styled with bold typography, a colored left border corresponding to severity, and an "unread dot" indicator.
    *   **Read Alert Item Element:** Muted text colors and transparent borders.
    *   **Alert Content:** Severity Icon, Title, Detailed Description, Timestamp (e.g., "2 hours ago").
    *   **Alert Action Row:** For each alert, buttons for: `Mark Read`, `Dismiss`, and `Ask CashPilot`.

### 3.4 History (Reports) View
A deeper dive into historical trends and past ingestions.

*   **Page Header Block:** "Financial History" and an "Export to PDF" button.
*   **Trends Chart Block:** A wide line chart plotting the historical changes in the Health Score over the past 12 months.
*   **Data Runs Table Block:**
    *   **Table Header:** `Date Uploaded`, `Filename`, `Status`, `Key Insight Snippet`.
    *   **Table Rows:** Data populated from the API.
    *   **Pagination/Infinite Scroll Element:** To navigate older records.

### 3.5 Settings View
*   **Profile Settings Block:** Form fields for User Name, Email, and Avatar upload.
*   **Business Profile Block:** Form fields for Company Name, Industry category dropdown, and Default Currency select.
*   **Integrations Block:**
    *   **Stripe / API Key Inputs:** Secure input fields (password type with eye-toggle).
    *   **Connection Status:** "Connected" (green) or "Disconnected" (red) badges.
*   **Notification Settings Block:** Switch/Toggles for "Email alerts for Anomalies" and "Weekly Digest emails".

---

## 4. API & WebSocket Contracts
The frontend builder must wrap these in custom React hooks or data fetching libraries (e.g., SWR, React Query).

*   **WebSocket (`useWebSocket.ts`)**:
    *   `ws://.../ws`
    *   Events to handle: `alert` (triggers unread badge update), `analysis_progress`, `chat_tool_call`.
*   **REST Endpoints:**
    *   `POST /api/v1/chat` -> Receives message, returns response & used tools.
    *   `GET /api/v1/alerts` -> Returns array of alert objects.
    *   `PATCH /api/v1/alerts/{alert_id}/read` -> Updates read status.

---

## 5. Optimal Engineering Choices for Implementation
When generating the code, the AI tool MUST adhere to these strict choices:

1.  **Component Architecture:** Absolute strict modularity. `Snapshot.tsx` must not contain the DOM elements for the gauge; it must compose `<QuickStats />`, `<HealthScoreGauge />`, and `<AnomalyWidget />`. Components must reside in `src/components/`.
2.  **Tailwind Utility Organization (CVA):** Use `cva` (Class Variance Authority) to manage component states. Example: An `AlertBadge` component must use CVA to define `intent: "critical" | "warning" | "info"`, which maps to specific Tailwind background/text colors.
3.  **Class Merging:** Always wrap `className` props in a utility function: `cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }` to prevent Tailwind class conflicts.
4.  **Error Boundaries & Suspense:** Wrap major blocks in React Suspense with skeleton loaders (shimmering UI components) to handle async data fetching gracefully.
5.  **State Management:** Use standard React Context for global state like the current selected `business_id` or `Theme`.
6.  **Responsiveness:** Use Tailwind breakpoints (`md:`, `lg:`, `xl:`). The dashboard grid must collapse from a 4-column layout (`grid-cols-4`) on desktop to a 1-column layout (`grid-cols-1`) on mobile.
