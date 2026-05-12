# CashPilot — Exhaustive Frontend Product Requirements Document
### Version 1.0 | Engineering & Design Blueprint

---

## Table of Contents

1. [Product Vision & Design Philosophy](#1-product-vision--design-philosophy)
2. [Design System: The Full Token Set](#2-design-system-the-full-token-set)
   - 2.1 Color Palette
   - 2.2 Typography
   - 2.3 Spacing & Layout Grid
   - 2.4 Shadows & Elevation
   - 2.5 Border Radius
   - 2.6 Motion & Animation
3. [Engineering Architecture](#3-engineering-architecture)
   - 3.1 Project Directory Structure
   - 3.2 Core Utilities
   - 3.3 State Management Strategy
   - 3.4 Data Fetching Layer
   - 3.5 WebSocket Integration
   - 3.6 Error Boundaries & Suspense
4. [Application Shell](#4-application-shell)
   - 4.1 Sidebar (Desktop)
   - 4.2 Topbar (Mobile/Tablet)
   - 4.3 Data Upload Modal
5. [Page Specifications](#5-page-specifications)
   - 5.1 Snapshot (Dashboard)
   - 5.2 Chat (AI Co-pilot)
   - 5.3 Alerts Feed
   - 5.4 History (Reports)
   - 5.5 Settings
6. [Data Visualization Specs (All Charts)](#6-data-visualization-specs-all-charts)
7. [Component Library Catalogue](#7-component-library-catalogue)
8. [Accessibility & Responsiveness](#8-accessibility--responsiveness)
9. [Performance Budget](#9-performance-budget)
10. [Implementation Sequencing](#10-implementation-sequencing)

---

## 1. Product Vision & Design Philosophy

### 1.1 What CashPilot Is

CashPilot is a financial intelligence co-pilot for small businesses. Its users are busy founders and finance leads who need to absorb complex financial reality at a glance and then drill into specifics through conversation. The product must communicate *trust*, *clarity*, and *intelligence* simultaneously — these are not decorative goals but functional ones. A user who feels uncertain about a number they're reading will not act on it.

### 1.2 Aesthetic Direction: "Refined Command Center"

The chosen aesthetic is **Dark-first, data-dense, surgical precision**. Think Bloomberg Terminal meets Linear.app — high information density without claustrophobia, achieved through strict typographic hierarchy and precise use of color as signal (not decoration). The dark theme is the *primary* theme and should feel native, not an afterthought.

The one thing a user should remember: **every color on screen means something**. Green is safe. Amber is a warning. Red is an alarm. This is non-negotiable — decorative use of these colors anywhere undermines the product's signal system.

### 1.3 What This Document Is

This document is a complete implementation contract. It covers every design token, every component prop, every chart configuration, every API hook, and the engineering architecture that ties them together. If you are building CashPilot, you should be able to implement every screen from this document alone without needing to make stylistic decisions.

---

## 2. Design System: The Full Token Set

### 2.1 Color Palette

All colors are defined as CSS custom properties on `:root` and a `[data-theme="light"]` override. The dark theme is the default and does NOT require a `data-theme` attribute.

```css
/* === BASE SURFACES === */
--color-bg-base:       #0A0D13;   /* Page background — near black with a blue tint */
--color-bg-raised:     #0F1420;   /* Cards, panels resting on the base */
--color-bg-elevated:   #161C2D;   /* Modals, dropdowns, popovers */
--color-bg-sunken:     #070A10;   /* Input fields, inset elements */
--color-bg-hover:      #1C2438;   /* Hover state for interactive surface items */

/* === BORDERS === */
--color-border-subtle:  #1E2740;  /* Dividers, card borders — barely visible */
--color-border-default: #283050;  /* Standard border on inputs and cards */
--color-border-strong:  #3D4E70;  /* Focused inputs, selected states */

/* === CONTENT (TEXT) === */
--color-text-primary:   #E8EBF4;  /* Main readable text */
--color-text-secondary: #8A94B0;  /* Labels, captions, secondary info */
--color-text-tertiary:  #525C78;  /* Placeholder text, disabled labels */
--color-text-inverse:   #0A0D13;  /* Text on bright backgrounds (e.g. primary buttons) */

/* === PRIMARY BRAND ACCENT === */
/* A cool electric blue — stands out against dark backgrounds without being neon */
--color-primary-50:    #EFF5FF;
--color-primary-100:   #DBEAFF;
--color-primary-200:   #BEDBFF;
--color-primary-300:   #91C4FE;
--color-primary-400:   #5CA4FC;
--color-primary-500:   #3B82F6;   /* Primary CTA background */
--color-primary-600:   #2563EB;   /* Primary CTA hover */
--color-primary-700:   #1D4ED8;
--color-primary-800:   #1E40AF;
--color-primary-900:   #1E3A8A;
--color-primary-950:   #172554;

/* === SEMANTIC: HEALTH SIGNAL SYSTEM === */
/* Green — Good / Safe / Positive */
--color-success-subtle:  #0A1F14;  /* Background tint for success states */
--color-success-muted:   #14532D;
--color-success-default: #22C55E;  /* Text and icon for good indicators */
--color-success-bright:  #4ADE80;  /* Bright callout numbers */

/* Amber — Warning / Needs Attention */
--color-warning-subtle:  #1C1200;
--color-warning-muted:   #78350F;
--color-warning-default: #F59E0B;
--color-warning-bright:  #FCD34D;

/* Red — Critical / Danger / High Risk */
--color-danger-subtle:   #1C0808;
--color-danger-muted:    #7F1D1D;
--color-danger-default:  #EF4444;
--color-danger-bright:   #F87171;

/* === CHART-SPECIFIC PALETTE === */
/* These are for data series; they must remain distinguishable even for color-blind users */
--color-chart-revenue:   #3B82F6;  /* Blue — Revenue line/area */
--color-chart-expense:   #F43F5E;  /* Rose — Expenses line/area */
--color-chart-profit:    #22C55E;  /* Green — Net Profit */
--color-chart-neutral:   #8B5CF6;  /* Violet — Neutral series or forecast */
--color-chart-grid:      #1E2740;  /* Chart gridlines — subtle */
--color-chart-axis:      #525C78;  /* Axis tick labels */

/* === SCROLLBAR === */
--color-scrollbar-thumb: #283050;
--color-scrollbar-track: #0A0D13;
```

**Light theme override** (applied via `[data-theme="light"]` on `<html>`):

```css
[data-theme="light"] {
  --color-bg-base:       #F0F4FA;
  --color-bg-raised:     #FFFFFF;
  --color-bg-elevated:   #FFFFFF;
  --color-bg-sunken:     #E8EDF5;
  --color-bg-hover:      #EBF0F9;
  --color-border-subtle: #DDE3F0;
  --color-border-default:#C4CDDF;
  --color-border-strong: #97A6C4;
  --color-text-primary:  #111827;
  --color-text-secondary:#4B5563;
  --color-text-tertiary: #9CA3AF;
  --color-text-inverse:  #FFFFFF;
  --color-chart-grid:    #E5EAF5;
  --color-chart-axis:    #9CA3AF;
  --color-scrollbar-thumb:#C4CDDF;
  --color-scrollbar-track:#F0F4FA;
}
```

### 2.2 Typography

CashPilot uses two typefaces, both loaded via Google Fonts or self-hosted to avoid FOUT (flash of unstyled text).

**Display & UI Font: `DM Sans`** — A geometric sans-serif with optical corrections that make it highly readable at small sizes while feeling modern and authoritative at large sizes. Used for all UI labels, nav items, buttons, and KPI numbers.

**Monospace Font: `JetBrains Mono`** — Used exclusively for financial figures (revenue amounts, percentages, health scores) in KPI cards. The tabular digit alignment prevents number wobble in live-updating components.

```css
/* Font imports */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Type scale — all in rem, base 16px */
--font-family-ui:    'DM Sans', system-ui, sans-serif;
--font-family-mono:  'JetBrains Mono', 'Fira Code', monospace;

--text-xs:    0.6875rem;  /* 11px — timestamps, legal copy */
--text-sm:    0.8125rem;  /* 13px — secondary labels, table cells */
--text-base:  0.9375rem;  /* 15px — body text, descriptions */
--text-md:    1.0625rem;  /* 17px — slightly emphasized body */
--text-lg:    1.1875rem;  /* 19px — section headers */
--text-xl:    1.375rem;   /* 22px — card titles, page sub-headers */
--text-2xl:   1.75rem;    /* 28px — page titles */
--text-3xl:   2.25rem;    /* 36px — KPI numbers (large) */
--text-4xl:   3rem;       /* 48px — hero KPI number (health score gauge center) */
--text-5xl:   3.75rem;    /* 60px — jumbo display (used sparingly) */

--font-weight-regular:  400;
--font-weight-medium:   500;
--font-weight-semibold: 600;
--font-weight-bold:     700;

--line-height-tight:    1.2;   /* Headings and big KPI numbers */
--line-height-snug:     1.35;  /* Card titles */
--line-height-normal:   1.5;   /* Body paragraphs */
--line-height-relaxed:  1.65;  /* Chat message bubbles, longer text */

--letter-spacing-tight: -0.02em;  /* Large KPI numbers */
--letter-spacing-normal: 0;
--letter-spacing-wide:   0.04em;  /* Uppercase labels, tags */
--letter-spacing-wider:  0.08em;  /* "CRITICAL" severity pills */
```

**Typography usage rules:**

KPI numbers (revenue, expense, profit, runway) must always render in `font-family: var(--font-family-mono)` with `font-variant-numeric: tabular-nums`. This prevents layout shift when numbers update and maintains column alignment in tables. All other text uses `--font-family-ui`.

Percentage change badges (`+12%`, `-3%`) are `text-sm`, `font-weight-semibold`, monospace. Section headers on pages (e.g., "Recent Anomalies") are `text-lg`, `font-weight-semibold`, primary text color. Page-level titles are `text-2xl`, `font-weight-bold`, primary text color.

### 2.3 Spacing & Layout Grid

CashPilot uses a **4px base grid**. Every spacing value is a multiple of 4.

```css
--space-1:   0.25rem;  /* 4px */
--space-2:   0.5rem;   /* 8px */
--space-3:   0.75rem;  /* 12px */
--space-4:   1rem;     /* 16px */
--space-5:   1.25rem;  /* 20px */
--space-6:   1.5rem;   /* 24px */
--space-8:   2rem;     /* 32px */
--space-10:  2.5rem;   /* 40px */
--space-12:  3rem;     /* 48px */
--space-16:  4rem;     /* 64px */
--space-20:  5rem;     /* 80px */
--space-24:  6rem;     /* 96px */
```

**Application Layout Grid:**

The root layout is a CSS Grid with named areas. On desktop (≥1024px):
- Sidebar: `240px` fixed width, full viewport height, `position: sticky; top: 0`.
- Main content area: `1fr`, scrollable.
- The grid is `display: grid; grid-template-columns: 240px 1fr; min-height: 100dvh`.

On tablet (768px–1023px): Sidebar collapses to a slide-out drawer; main content takes full width.

On mobile (<768px): Sidebar is a drawer. The topbar is `56px` tall. Content starts below it.

**Card padding:** `var(--space-6)` (24px) on all sides. On mobile: `var(--space-4)` (16px).

**Section gaps:** Vertical gap between major sections on a page is `var(--space-8)` (32px).

**KPI grid column gap:** `var(--space-4)` (16px) between cards.

### 2.4 Shadows & Elevation

Shadows are defined on a 4-level elevation system to communicate depth:

```css
--shadow-sm:  0 1px 2px rgba(0,0,0,0.4);                         /* Subtle card lift */
--shadow-md:  0 4px 12px rgba(0,0,0,0.5), 0 1px 3px rgba(0,0,0,0.3);  /* Standard cards */
--shadow-lg:  0 8px 24px rgba(0,0,0,0.6), 0 2px 6px rgba(0,0,0,0.4);  /* Modals, dropdowns */
--shadow-xl:  0 20px 60px rgba(0,0,0,0.7), 0 4px 12px rgba(0,0,0,0.5); /* Fullscreen overlays */

/* Colored glow shadows — used on critical state cards only */
--shadow-danger:  0 0 20px rgba(239,68,68,0.15), 0 4px 12px rgba(0,0,0,0.5);
--shadow-success: 0 0 20px rgba(34,197,94,0.12), 0 4px 12px rgba(0,0,0,0.5);
--shadow-primary: 0 0 20px rgba(59,130,246,0.2), 0 4px 12px rgba(0,0,0,0.5);
```

When a Cash Runway card drops below 3 months, its card shadow switches from `--shadow-md` to `--shadow-danger`. When health score is >80, the gauge card gets `--shadow-success`.

### 2.5 Border Radius

```css
--radius-sm:   4px;    /* Tags, pills, inline badges */
--radius-md:   8px;    /* Inputs, small buttons, table rows */
--radius-lg:   12px;   /* Cards, panels */
--radius-xl:   16px;   /* Modals */
--radius-2xl:  24px;   /* Large chart containers */
--radius-full:  9999px; /* Circular avatars, toggle switches */
```

### 2.6 Motion & Animation

All transitions use a consistent easing curve to feel physically coherent.

```css
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);   /* Page transitions, sidebar slide */
--ease-in-out:    cubic-bezier(0.4, 0, 0.2, 1);     /* Standard UI interactions */
--ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1); /* Bouncy — for success states */

--duration-instant: 80ms;   /* Button press feedback */
--duration-fast:   150ms;   /* Hover state color transitions */
--duration-normal: 250ms;   /* Standard open/close transitions */
--duration-slow:   400ms;   /* Page-level transitions */
--duration-enter:  600ms;   /* First-load staggered reveals */
```

**Animation rules:**

The `prefers-reduced-motion` media query must be respected. Wrap all non-essential animations in `@media (prefers-reduced-motion: no-preference)`. The typing indicator (3-dot animation in Chat) is exempt from reduction since it communicates active state.

Staggered card entry on Snapshot: when the page first loads, the four KPI cards animate in with `opacity: 0 → 1` and `translateY(12px) → translateY(0)`, staggered by 80ms per card. Duration is 400ms with `--ease-out-expo`.

Typing indicator: three dots, each using a `scale(1) → scale(1.3) → scale(1)` keyframe, offset by 150ms each, repeating at 900ms total duration.

---

## 3. Engineering Architecture

### 3.1 Project Directory Structure

```
src/
├── components/           # All shared/reusable UI components
│   ├── ui/               # Atomic primitives (Button, Badge, Input, Card, etc.)
│   ├── charts/           # All Recharts wrappers (RevenueExpenseChart, SparkLine, etc.)
│   ├── layout/           # Shell components (Sidebar, Topbar, AppShell)
│   └── modals/           # Dialog wrappers (UploadModal, ConfirmModal)
│
├── features/             # Feature modules — each page has its own folder
│   ├── snapshot/         # Dashboard
│   │   ├── Snapshot.tsx              # Page composition only — no DOM elements
│   │   ├── components/
│   │   │   ├── QuickStats.tsx        # 4 KPI cards
│   │   │   ├── KPICard.tsx           # Individual KPI card
│   │   │   ├── HealthScoreGauge.tsx  # Donut gauge
│   │   │   ├── RevenueExpenseChart.tsx  # Primary P&L chart
│   │   │   ├── AnomalyWidget.tsx     # Live anomaly feed
│   │   │   └── RunwayBar.tsx         # Cash runway progress bar
│   │   └── hooks/
│   │       └── useSnapshotData.ts
│   ├── chat/
│   │   ├── Chat.tsx
│   │   ├── components/
│   │   │   ├── MessageFeed.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ToolCallPill.tsx
│   │   │   ├── TypingIndicator.tsx
│   │   │   ├── SuggestedPrompts.tsx
│   │   │   └── ChatInput.tsx
│   │   └── hooks/
│   │       └── useChatSession.ts
│   ├── alerts/
│   │   ├── Alerts.tsx
│   │   ├── components/
│   │   │   ├── AlertList.tsx
│   │   │   ├── AlertItem.tsx
│   │   │   └── AlertFilters.tsx
│   │   └── hooks/
│   │       └── useAlerts.ts
│   ├── history/
│   │   ├── History.tsx
│   │   ├── components/
│   │   │   ├── HealthScoreHistory.tsx
│   │   │   └── DataRunsTable.tsx
│   │   └── hooks/
│   │       └── useHistory.ts
│   └── settings/
│       ├── Settings.tsx
│       └── components/
│           ├── ProfileForm.tsx
│           ├── BusinessProfileForm.tsx
│           ├── IntegrationCard.tsx
│           └── NotificationToggles.tsx
│
├── hooks/                # Global custom hooks
│   ├── useWebSocket.ts
│   ├── useTheme.ts
│   └── useUploadModal.ts
│
├── store/                # React Context stores
│   ├── AppContext.tsx    # business_id, theme, global UI state
│   └── AlertsContext.tsx # Unread alert count (drives badge)
│
├── lib/                  # Pure utilities
│   ├── cn.ts             # Tailwind class merging utility
│   ├── formatters.ts     # Currency, percentage, date formatting
│   ├── api.ts            # REST client (base fetch wrapper)
│   └── constants.ts      # API_BASE_URL, WS_URL, etc.
│
├── types/                # TypeScript interfaces for all domain objects
│   ├── alert.ts
│   ├── snapshot.ts
│   ├── chat.ts
│   └── report.ts
│
└── styles/
    ├── globals.css       # CSS custom properties, base resets
    └── typography.css    # Prose styles for markdown rendering
```

### 3.2 Core Utilities

**`cn.ts` — Class Merging Utility**

Every component that accepts a `className` prop must route it through `cn()`. This prevents Tailwind class conflicts (e.g., two `text-*` classes colliding).

```typescript
// src/lib/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

**`formatters.ts` — Consistent Financial Formatting**

All financial numbers in the app must pass through these formatters. Never format currency or percentages inline in JSX.

```typescript
// src/lib/formatters.ts

export function formatCurrency(
  value: number,
  currency: string = 'USD',
  compact: boolean = false
): string {
  if (compact && Math.abs(value) >= 1_000_000) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency,
      notation: 'compact', maximumFractionDigits: 1
    }).format(value);
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency,
    minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(value);
}

export function formatPercent(value: number, decimals: number = 1): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

export function formatMonths(value: number): string {
  return `${value.toFixed(1)} mo`;
}

export function formatRelativeTime(isoString: string): string {
  // Returns "2 hours ago", "just now", etc.
  const diff = Date.now() - new Date(isoString).getTime();
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}
```

### 3.3 State Management Strategy

CashPilot does not use Redux or Zustand. The state is categorized and managed as follows:

**Global Context (`AppContext`)** — holds `businessId` (string), `theme` ("dark" | "light"), `isUploadModalOpen` (boolean), `lastSyncedAt` (string | null). This wraps the entire app. Theme changes trigger the `data-theme` attribute on `<html>`.

**Alerts Context (`AlertsContext`)** — holds `unreadCount` (number), updated both by the initial `GET /api/v1/alerts` fetch and by incoming `alert` WebSocket events. The Sidebar nav badge subscribes to this context.

**Server state** (API responses) is managed with **React Query (`@tanstack/react-query`)**. This handles caching, background refetching, loading states, and error states for all REST calls. Never use raw `useEffect` + `useState` for data fetching.

**Local UI state** (which time period toggle is active on the chart, filter dropdown value, etc.) lives in `useState` within the component that owns it — it is never lifted above what is necessary.

**Chat session** — `sessionId` is stored in `sessionStorage` (not `localStorage`) so it survives page navigation within a tab but resets on new tabs. The message history array is held in `useState` in `Chat.tsx` and passed down.

### 3.4 Data Fetching Layer

```typescript
// src/lib/api.ts — Base REST client

const API_BASE = import.meta.env.VITE_API_BASE_URL;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      // auth header injected here from token store
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  get:   <T>(path: string)                      => request<T>(path),
  post:  <T>(path: string, body: unknown)        => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown)       => request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
};
```

**React Query hooks pattern** (one per feature):

```typescript
// src/features/alerts/hooks/useAlerts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Alert } from '@/types/alert';

export function useAlerts() {
  return useQuery<Alert[]>({
    queryKey: ['alerts'],
    queryFn: () => api.get('/api/v1/alerts'),
    staleTime: 30_000,   // Don't refetch if data is <30s old
    refetchOnWindowFocus: true,
  });
}

export function useMarkAlertRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => api.patch(`/api/v1/alerts/${alertId}/read`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  });
}
```

### 3.5 WebSocket Integration

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from 'react';

type WSEvent = 'alert' | 'analysis_progress' | 'chat_tool_call';
type Handler = (payload: unknown) => void;

export function useWebSocket(handlers: Partial<Record<WSEvent, Handler>>) {
  const ws = useRef<WebSocket | null>(null);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers; // always use latest handlers without re-subscribing

  useEffect(() => {
    const socket = new WebSocket(import.meta.env.VITE_WS_URL);
    ws.current = socket;

    socket.onmessage = (event) => {
      try {
        const { type, payload } = JSON.parse(event.data);
        handlersRef.current[type as WSEvent]?.(payload);
      } catch { /* malformed message — log in dev */ }
    };

    socket.onclose = () => {
      // Exponential backoff reconnect logic here
    };

    return () => socket.close();
  }, []); // empty deps: connect once on mount

  return ws;
}
```

The `AppShell` component is the only place that calls `useWebSocket`. It dispatches incoming `alert` events to `AlertsContext` (incrementing `unreadCount`) and `analysis_progress` events to a toast notification system.

### 3.6 Error Boundaries & Suspense

Every major feature section is wrapped in a `<FeatureBoundary>` component that composes `<ErrorBoundary>` + `<Suspense>` with a skeleton fallback:

```typescript
// src/components/FeatureBoundary.tsx
<ErrorBoundary fallback={<ErrorState />}>
  <Suspense fallback={<SkeletonLoader variant={variant} />}>
    {children}
  </Suspense>
</ErrorBoundary>
```

The `<SkeletonLoader>` renders animated shimmering placeholders. The shimmer animation is:

```css
@keyframes shimmer {
  from { background-position: -400px 0; }
  to   { background-position:  400px 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-raised) 25%,
    var(--color-bg-hover)  50%,
    var(--color-bg-raised) 75%
  );
  background-size: 800px 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-md);
}
```

The `variant` prop on `<SkeletonLoader>` accepts `"kpi-grid"`, `"chart"`, `"list"`, `"table"` to render appropriately shaped skeletons matching the real content.

---

## 4. Application Shell

### 4.1 Sidebar (Desktop)

The sidebar is `240px` wide, sticky, full viewport height. Background: `var(--color-bg-raised)`. Right border: `1px solid var(--color-border-subtle)`. The sidebar is a CSS Grid layout with three rows: brand header (auto), nav menu (1fr), user profile (auto).

**Brand Header** (`height: 64px`): Contains a `💰` emoji rendered at `20px` in a `28px × 28px` container, followed by the text "CashPilot" in `text-xl`, `font-weight-bold`, `color: var(--color-text-primary)`. Padding: `var(--space-6)` horizontal. A bottom border `1px solid var(--color-border-subtle)` separates it from the nav.

**Primary Nav Menu**: `padding: var(--space-4)`. Each nav item is a flexbox row with `gap: var(--space-3)`, `height: 40px`, `padding: 0 var(--space-3)`, `border-radius: var(--radius-md)`. The icon is `18px × 18px` Lucide icon. The label is `text-sm`, `font-weight-medium`.

**Nav item states:**
- Default (inactive): `color: var(--color-text-secondary)`. Background: transparent.
- Hover: Background `var(--color-bg-hover)`. Color: `var(--color-text-primary)`. Transition `150ms`.
- Active (current page): Background `rgba(59,130,246,0.12)`. Color `var(--color-primary-400)`. A `2px` left border on the nav item container using `var(--color-primary-500)`.

**Alerts Badge**: Positioned absolutely on the Bell icon. Background `var(--color-danger-default)`. `min-width: 18px`, `height: 18px`, `border-radius: var(--radius-full)`, `font-size: 10px`, `font-weight-bold`. Shows the number; if >99 shows "99+". The badge animates with `scale(0) → scale(1)` when the count first appears (spring ease, 200ms).

**User Profile Snippet** (bottom of sidebar): A `56px` tall row with `padding: var(--space-4)`. Contains a `32px` avatar (initials fallback with `background: var(--color-primary-800)`, white text), user name in `text-sm font-weight-medium`, and email in `text-xs color: var(--color-text-tertiary)`, truncated with ellipsis.

**Theme Toggle**: Immediately above the user profile. A `40px` wide pill switch. Sun icon (light) / Moon icon (dark) at `14px`. Background toggles between `var(--color-bg-sunken)` and `var(--color-primary-900)`. The thumb slides with a `200ms ease-in-out` transition.

### 4.2 Topbar (Mobile/Tablet)

Height: `56px`. Background: `var(--color-bg-raised)`. Bottom border: `1px solid var(--color-border-subtle)`. `position: sticky; top: 0; z-index: 50`.

Contains three elements: Hamburger button (left), "CashPilot" brand text (center), "Upload" button (right, primary button style, compact).

The slide-out drawer that opens from the hamburger: `width: 280px`, `background: var(--color-bg-raised)`, overlays the content with a `backdrop-filter: blur(4px)` scrim behind it. Drawer slides in from left with `--ease-out-expo` in `300ms`. Pressing outside or pressing the X closes it (reverse animation).

### 4.3 Data Upload Modal

Triggered by the "Upload Data" button in the topbar or any equivalent CTA. Uses a Radix UI `Dialog`.

**Modal container**: `max-width: 520px`, `width: 90vw`, `background: var(--color-bg-elevated)`, `border-radius: var(--radius-xl)`, `box-shadow: var(--shadow-xl)`, `border: 1px solid var(--color-border-default)`. Entry animation: scale from 0.95 to 1.0 with opacity 0→1, `300ms`, `--ease-out-expo`.

**Drag & Drop Zone**: `height: 180px`, `border: 2px dashed var(--color-border-default)`, `border-radius: var(--radius-lg)`, `background: var(--color-bg-sunken)`. Center content: `Upload` icon (32px, `color: var(--color-text-tertiary)`), primary text "Drag & drop your CSV here" in `text-base`, secondary text "or click to browse" in `text-sm text-tertiary`.

**Drag-over state**: Border changes to `var(--color-primary-500)`, background to `rgba(59,130,246,0.06)`. The icon scales up to `1.1` over `150ms`.

**File selected state**: Hides the drag zone; shows filename (truncated to 30 chars), file size, and a remove (×) button. A `CheckCircle` icon in `var(--color-success-default)` precedes the filename.

**Upload progress bar**: Full-width, `height: 4px`, `border-radius: var(--radius-full)`. Track: `var(--color-bg-hover)`. Fill: gradient from `var(--color-primary-500)` to `var(--color-primary-300)`. The fill width transitions with `transition: width 150ms ease-in-out`.

**Analysis status**: Shown after file upload completes. A spinner (CSS `border` animation, 24px, border `var(--color-primary-500)`) next to the text "CashPilot is analyzing your data..." in `text-base italic text-secondary`. A step tracker below shows 3 steps: "Parsing", "Running analysis", "Generating insights" — each has a circle status indicator.

---

## 5. Page Specifications

### 5.1 Snapshot (Dashboard)

`Snapshot.tsx` is a composition-only component. It renders:

```tsx
// src/features/snapshot/Snapshot.tsx — the ONLY content here is this JSX
return (
  <main className="p-8 space-y-8">
    <PageHeader title="Financial Snapshot" />
    <FeatureBoundary variant="kpi-grid">
      <QuickStats />
    </FeatureBoundary>
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <FeatureBoundary variant="chart" className="xl:col-span-2">
        <RevenueExpenseChart />
      </FeatureBoundary>
      <FeatureBoundary variant="chart">
        <HealthScoreGauge />
      </FeatureBoundary>
    </div>
    <FeatureBoundary variant="list">
      <AnomalyWidget />
    </FeatureBoundary>
  </main>
);
```

**Page Header Block:**
The `PageHeader` component: Title "Financial Snapshot" in `text-2xl font-bold`. Subtitle "Last synced: [formatted timestamp]" in `text-sm text-secondary`. Right-aligned: `RefreshCw` icon button (24px, `text-secondary`). On hover, the icon rotates 360° over `600ms`. While data is loading after click, the icon spins continuously.

**KPI Summary Grid (`QuickStats`):**
`display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px`. On `lg` and below: `grid-cols-2`. On `sm` and below: `grid-cols-1`.

Each `KPICard` component: `background: var(--color-bg-raised)`, `border: 1px solid var(--color-border-subtle)`, `border-radius: var(--radius-lg)`, `padding: var(--space-6)`, `box-shadow: var(--shadow-md)`.

**`KPICard` internal layout:**
- Top row: Card title label in `text-sm font-medium text-secondary uppercase tracking-wide` (left). Trend icon (right) — `TrendingUp` or `TrendingDown` Lucide icon, `16px`, colored by trend.
- Middle: Big number in `text-3xl font-semibold font-mono letter-spacing-tight`. Renders as skeleton pulse while loading.
- Bottom row: Sparkline chart (left, 80px × 32px) + MoM change badge (right).

**MoM Change Badge (`TrendBadge`):** CVA-controlled component.

```typescript
const trendBadge = cva(
  'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold font-mono',
  {
    variants: {
      direction: {
        positive: 'bg-success-subtle text-success-bright',
        negative: 'bg-danger-subtle text-danger-bright',
        neutral:  'bg-bg-hover text-secondary',
      }
    }
  }
);
```

**Total Revenue Card**: Number formatted as compact currency (e.g., `$1.2M`). Trend badge shows MoM revenue % change. Positive is green (good).

**Total Expenses Card**: Number formatted as compact currency. Trend badge: positive (expenses increasing) is **red** (bad). Negative (expenses decreasing) is **green** (good). This is intentionally inverted from revenue.

**Net Profit Margin Card**: Displayed as a percentage (e.g., `24.7%`). Badge shows the change in percentage points (e.g., `+2.3pp`). A right-pointing trend arrow — green for up, red for down.

**Cash Runway Card**: Displayed as `X.X mo` in `--font-family-mono`. The color of this number changes dynamically: green if >6 months, amber if 3-6 months, red if <3 months. Below the number, a `RunwayBar` component: a horizontal bar `height: 6px`, `border-radius: var(--radius-full)`, `background: var(--color-bg-hover)`. The fill uses a `linear-gradient` from `var(--color-success-default)` (left) through `var(--color-warning-default)` to `var(--color-danger-default)` (right), showing the entire gradient as the track. An indicator thumb sits at the position corresponding to the runway value relative to a 12-month max. When runway < 3 months, the card shadow switches to `--shadow-danger`.

**Sparkline (micro-chart)**: `TinySparkLine` component wraps Recharts `<ResponsiveContainer width="100%" height={32}>` containing a `<AreaChart>` with no axes, no grid, no tooltip. The area fill is a subtle gradient from the line color at 30% opacity to 0% opacity. Line stroke: `1.5px`. No dots on data points.

**Primary Chart Block (`RevenueExpenseChart`):**
Full spec in Section 6. Card header: "Revenue vs. Expenses" in `text-lg font-semibold`. Time period toggles are a group of buttons: `1M | 3M | 6M | YTD | All`. Active toggle: `background: var(--color-primary-600)`, `color: white`, `border-radius: var(--radius-sm)`. Inactive: `background: transparent`, `color: var(--color-text-secondary)`, hover shows `var(--color-bg-hover)`. The button group has `background: var(--color-bg-sunken)` and `border-radius: var(--radius-md)` as a container.

**Health Score Gauge (`HealthScoreGauge`):**
Full spec in Section 6. Card below the gauge: Status label maps score to text and color:
- 70–100: "Healthy" in `var(--color-success-default)`.
- 40–69: "Needs Attention" in `var(--color-warning-default)`.
- 0–39: "At Risk" in `var(--color-danger-default)`.

The score number animates from 0 to its actual value using a `requestAnimationFrame` counter over `800ms` on first mount (eased).

**Live Anomaly Feed (`AnomalyWidget`):**
Card header: "Recent Anomalies" + a `Live` pill (pulsing red dot + "LIVE" text in `text-xs font-bold`). The pulsing dot is a CSS keyframe: `opacity: 1 → 0.3 → 1` at 1.5s interval.

Each anomaly list item: `padding: var(--space-4)`, `border-bottom: 1px solid var(--color-border-subtle)`. Last item has no border. Contains: Severity icon (left, 20px), Title in `text-sm font-medium`, Date in `text-xs text-tertiary`, Severity pill (right). Each row has an "Ask CashPilot →" ghost link button that, on click, navigates to `/chat` and pre-populates the chat input via `sessionStorage` with a context string like "Tell me more about: [anomaly title]".

**Severity pill (`AlertBadge`):** CVA component:

```typescript
const alertBadge = cva(
  'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider',
  {
    variants: {
      intent: {
        critical: 'bg-danger-subtle  text-danger-bright  border border-danger-muted',
        warning:  'bg-warning-subtle text-warning-bright border border-warning-muted',
        info:     'bg-primary-950   text-primary-300    border border-primary-800',
      }
    }
  }
);
```

### 5.2 Chat (AI Co-pilot View)

**Layout:** Two-column stack — full height of viewport minus topbar. Top section (flexible height): message feed. Bottom: fixed input area.

```
┌─────────────────────────────────────────────┐
│ Page Header: "Chat with CashPilot"   [Clear] │
│──────────────────────────────────────────────│
│                                              │
│   [Message Feed — scrollable, flex-col]      │
│                                              │
│──────────────────────────────────────────────│
│   [Input Area — sticky bottom]               │
└─────────────────────────────────────────────┘
```

**Page header**: "Chat with CashPilot" in `text-2xl font-bold`. Right: "Clear Session" button with `Trash2` icon, `text-sm`, ghost variant (no background, `text-tertiary`, hover `text-danger-default`).

**Empty state**: A centered column with a `60px` animated CashPilot logo (the `💰` emoji in a pulsing gradient circle), "How can I help you analyze your finances today?" in `text-xl font-medium text-secondary`. Below: three suggested prompt pills in a flex-wrap row. Each pill: `background: var(--color-bg-raised)`, `border: 1px solid var(--color-border-default)`, `border-radius: var(--radius-full)`, `padding: var(--space-2) var(--space-4)`, `text-sm text-secondary`. Hover: border becomes `var(--color-primary-500)`, text becomes `var(--color-primary-400)`. Clicking sends the message instantly.

**Message Feed (`MessageFeed`):** `flex-1 overflow-y-auto scroll-smooth`. Padding `var(--space-6)`. Gap between messages: `var(--space-4)`. Scroll to bottom behavior: on new message, `scrollIntoView({ behavior: 'smooth' })` is called on a sentinel div at the bottom of the list. Custom scrollbar: `width: 4px`, `background: var(--color-scrollbar-thumb)`, `border-radius: var(--radius-full)`.

**User Message Bubble:** `align-self: flex-end`, `max-width: 70%`, `background: var(--color-primary-700)`, `color: white`, `border-radius: 16px 16px 4px 16px`, `padding: var(--space-3) var(--space-4)`. Font: `text-base line-height-relaxed`. Accompanied by a right-side avatar placeholder.

**Agent Message Bubble:** `align-self: flex-start`, `max-width: 80%`, `background: var(--color-bg-elevated)`, `border: 1px solid var(--color-border-subtle)`, `border-radius: 4px 16px 16px 16px`, `padding: var(--space-4)`. Left-side CashPilot avatar (the `💰` logo, `28px`).

**Markdown Rendering:** Agent messages pass their `content` through `react-markdown` with `remark-gfm`. Custom Tailwind prose overrides ensure dark-theme compatibility. Tables render with `border-collapse: collapse`, each cell gets `border: 1px solid var(--color-border-default)`, `padding: var(--space-2) var(--space-3)`. Table header row: `background: var(--color-bg-hover)`, `font-weight-semibold`. Code blocks inside messages: `background: var(--color-bg-sunken)`, `font-family: --font-family-mono`, `border-radius: var(--radius-md)`, `padding: var(--space-4)`.

**Tool Execution Pill (`ToolCallPill`):** Appears as part of the agent message, above the text response. `background: rgba(139,92,246,0.1)`, `border: 1px solid rgba(139,92,246,0.3)`, `border-radius: var(--radius-sm)`, `padding: var(--space-1) var(--space-3)`, `text-xs font-mono text-violet-400`. Leading `🔧` icon. When a tool call is in-progress (streaming), the pill shows a pulsing shimmer animation. When complete, it shows a `CheckCircle` icon.

**Typing Indicator (`TypingIndicator`):** Rendered as an agent bubble with only the three-dot animation inside. Three `6px` dots, `background: var(--color-text-tertiary)`, `border-radius: var(--radius-full)`. Each dot: `animation: bounce 0.9s ease-in-out infinite` with delays of 0ms, 150ms, 300ms.

**Input Area:** `border-top: 1px solid var(--color-border-subtle)`, `padding: var(--space-4) var(--space-6)`, `background: var(--color-bg-base)`. Contains a rounded input container: `background: var(--color-bg-raised)`, `border: 1px solid var(--color-border-default)`, `border-radius: var(--radius-xl)`, `padding: var(--space-3) var(--space-4)`. Focus: border becomes `var(--color-primary-500)`, `box-shadow: 0 0 0 3px rgba(59,130,246,0.15)`.

**Expanding Textarea:** `resize: none`, `min-height: 24px`, `max-height: 200px`. Auto-grow via JavaScript: on `input` event, reset height to `auto` then set height to `scrollHeight`. Background transparent, no border, no outline.

**Send Button:** Right side of the input container. When idle: `ArrowUp` icon in a `36px × 36px` circle, `background: var(--color-primary-600)`, white icon. When text is empty: `background: var(--color-bg-hover)`, icon dimmed — not clickable. When a response is streaming: transforms to a `Square` (stop) icon, `background: var(--color-danger-subtle)`, `color: var(--color-danger-default)`. Transition between states: `150ms`.

**Keyboard behavior:** `Enter` sends the message. `Shift+Enter` inserts a newline. `Escape` clears the input.

### 5.3 Alerts Feed View

**Page header:** "System Alerts" + "Mark all as read" ghost button (`text-sm`, `color: var(--color-primary-400)`).

**Filter row:** `display: flex; gap: 12px; flex-wrap: wrap`. Two elements: Severity filter (custom select dropdown) and Sort order dropdown. Both dropdowns: `background: var(--color-bg-raised)`, `border: 1px solid var(--color-border-default)`, `border-radius: var(--radius-md)`, `height: 36px`, `padding: 0 var(--space-3)`, `text-sm`. Open state renders a Radix UI `Select` popover with `background: var(--color-bg-elevated)`, `box-shadow: var(--shadow-lg)`.

**Alert List:** `display: flex; flex-direction: column; gap: 0`. No gap between items; they share borders. The list card has `background: var(--color-bg-raised)`, `border-radius: var(--radius-lg)`, `border: 1px solid var(--color-border-subtle)`, `overflow: hidden`.

**Unread Alert Item:** Left border `3px solid [severity color]`. Background `var(--color-bg-raised)`. Title: `text-sm font-semibold text-primary`. The "unread dot": `8px` circle in severity color, positioned at top-right of the title row. `padding: var(--space-4) var(--space-5)`.

**Read Alert Item:** Left border `3px solid transparent`. Background `var(--color-bg-base)`. Title: `text-sm font-medium text-secondary`. No unread dot.

**Alert content layout:**
```
[SeverityIcon 20px]  [Title text-sm font-semibold]           [RelativeTime text-xs text-tertiary]
                     [Description text-xs text-secondary]     [AlertBadge]
                     [Action buttons row: Mark Read | Dismiss | Ask CashPilot →]
```

**Alert action buttons:** Each is `text-xs`, ghost style with icon. "Mark Read" uses `Check` icon, "Dismiss" uses `X` icon, "Ask CashPilot" uses `MessageSquare` icon. They appear on hover of the row (via `group-hover:opacity-100` from `opacity-0`). On mobile they're always visible.

**Dismissing an alert:** The item animates out with `height → 0, opacity → 0, margin-top → 0` over `250ms` before being removed from the list. This prevents the jarring jump of items shifting position.

### 5.4 History (Reports) View

**Page header:** "Financial History" + "Export to PDF" button (outlined button, `Download` icon, `text-sm`).

**Health Score History chart:** Full spec in Section 6. A full-width card, `height: 280px` chart area.

**Data Runs Table:** `background: var(--color-bg-raised)`, `border-radius: var(--radius-lg)`, `border: 1px solid var(--color-border-subtle)`. Table element: `width: 100%`, `border-collapse: separate`, `border-spacing: 0`.

Table headers: `text-xs uppercase tracking-wider text-tertiary font-semibold`, `padding: var(--space-3) var(--space-5)`, `border-bottom: 1px solid var(--color-border-subtle)`, `background: var(--color-bg-sunken)`. Sticky to top when table scrolls.

Table rows: `border-bottom: 1px solid var(--color-border-subtle)`, `padding: var(--space-4) var(--space-5)`. Hover: `background: var(--color-bg-hover)`. The status column uses a colored pill badge: `Completed` in success style, `Processing` in warning style (with a spinning indicator), `Failed` in danger style.

Key Insight Snippet column: truncated to 1 line with `text-ellipsis overflow-hidden whitespace-nowrap`, `max-width: 280px`. On hover, shows a tooltip with the full text.

Pagination: `display: flex; justify-content: space-between; align-items: center; padding: 16px 20px`. Left: "Showing X–Y of Z results" in `text-sm text-secondary`. Right: `<Prev | 1 | 2 | 3 | ... | N | Next>` navigation, each page button `32px × 32px`, `border-radius: var(--radius-md)`. Active page: `background: var(--color-primary-600)`, white text.

### 5.5 Settings View

Settings is organized into card sections with `gap: var(--space-6)` between them. Each section card: `background: var(--color-bg-raised)`, `border: 1px solid var(--color-border-subtle)`, `border-radius: var(--radius-lg)`, `padding: var(--space-6)`.

Section title: `text-lg font-semibold`, bottom border `1px solid var(--color-border-subtle)` at `padding-bottom: var(--space-4) margin-bottom: var(--space-5)`.

**Form fields:** Label: `text-sm font-medium text-secondary`, `margin-bottom: var(--space-2)`. Input: `width: 100%`, `height: 40px`, `background: var(--color-bg-sunken)`, `border: 1px solid var(--color-border-default)`, `border-radius: var(--radius-md)`, `padding: 0 var(--space-3)`, `text-sm text-primary`. Focus: border `var(--color-primary-500)`, `box-shadow: 0 0 0 3px rgba(59,130,246,0.15)`. Error state: border `var(--color-danger-default)`, error message in `text-xs text-danger-bright` below the field.

**API Key fields:** `input[type="password"]`. Eye toggle (`Eye`/`EyeOff` Lucide icon, `16px`) positioned inside the input on the right side. On toggle: the input type switches between `password` and `text`.

**Connection Status badge:** `Connected` — small `CheckCircle` icon in `var(--color-success-default)` + "Connected" text. `Disconnected` — `XCircle` icon in `var(--color-danger-default)`. These sit on the same row as the integration card title.

**Notification Toggles:** Each toggle is a `Switch` component — a 36px × 20px pill. Default off: `background: var(--color-border-strong)`. On: `background: var(--color-primary-500)`. Thumb: `16px` white circle, transitions with `transform: translateX()` over `150ms`. The label and description sit to the left of the toggle.

---

## 6. Data Visualization Specs (All Charts)

### 6.1 Revenue vs. Expenses Area Chart

**Component:** `RevenueExpenseChart.tsx` using Recharts `<AreaChart>`.

**Chart type:** Stacked Area Chart — Revenue as the lower series, Expenses overlaid. The "fill" between them conveys profit (or loss) visually.

**Recharts configuration:**

```tsx
<ResponsiveContainer width="100%" height={320}>
  <AreaChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
    <defs>
      {/* Revenue area gradient */}
      <linearGradient id="gradRevenue" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.3} />
        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}   />
      </linearGradient>
      {/* Expense area gradient */}
      <linearGradient id="gradExpense" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%"  stopColor="#F43F5E" stopOpacity={0.2} />
        <stop offset="95%" stopColor="#F43F5E" stopOpacity={0}   />
      </linearGradient>
    </defs>

    <CartesianGrid
      strokeDasharray="3 3"
      stroke="var(--color-chart-grid)"
      vertical={false}   {/* Horizontal gridlines only */}
    />

    <XAxis
      dataKey="date"
      tickFormatter={formatAxisDate}  {/* "Jan", "Feb", etc. */}
      tick={{ fill: 'var(--color-chart-axis)', fontSize: 11 }}
      axisLine={false}
      tickLine={false}
    />

    <YAxis
      tickFormatter={(v) => formatCurrency(v, 'USD', true)}
      tick={{ fill: 'var(--color-chart-axis)', fontSize: 11 }}
      axisLine={false}
      tickLine={false}
      width={64}
    />

    <Tooltip content={<CustomChartTooltip />} cursor={{ stroke: 'var(--color-border-strong)', strokeWidth: 1 }} />

    <Area
      type="monotone"
      dataKey="revenue"
      stroke="#3B82F6"
      strokeWidth={2}
      fill="url(#gradRevenue)"
      dot={false}
      activeDot={{ r: 4, fill: '#3B82F6', stroke: '#fff', strokeWidth: 2 }}
    />

    <Area
      type="monotone"
      dataKey="expenses"
      stroke="#F43F5E"
      strokeWidth={2}
      fill="url(#gradExpense)"
      dot={false}
      activeDot={{ r: 4, fill: '#F43F5E', stroke: '#fff', strokeWidth: 2 }}
    />
  </AreaChart>
</ResponsiveContainer>
```

**Custom Tooltip (`CustomChartTooltip`):** `background: var(--color-bg-elevated)`, `border: 1px solid var(--color-border-default)`, `border-radius: var(--radius-md)`, `padding: var(--space-3) var(--space-4)`, `box-shadow: var(--shadow-lg)`. Content: Date heading in `text-xs text-secondary font-semibold`, then two rows: Revenue row (blue dot + "Revenue" label + formatted value), Expenses row (rose dot + "Expenses" label + formatted value). A third calculated row: Net Profit/Loss in success or danger color.

**Chart Legend:** Custom — a flex row below the card header, not Recharts' built-in legend. Each entry: a colored `10px × 3px` rounded rect followed by the series name in `text-xs text-secondary`. The Revenue and Expense legend items each show the latest point value in `text-xs font-mono font-semibold` in their respective color.

**Time period toggle behavior:** Changing the period triggers a React Query refetch with the new range param. During loading, the chart area shows the old data at 40% opacity with a loading shimmer overlay.

### 6.2 Health Score Gauge (Donut Chart)

**Component:** `HealthScoreGauge.tsx` using Recharts `<PieChart>` in donut mode.

The gauge is a **semicircular arc** (180° sweep), not a full circle. This is achieved by rendering only the top half of the donut.

```tsx
<PieChart width={240} height={130}>
  <Pie
    data={[
      { value: score },         // filled arc
      { value: 100 - score },   // empty arc
    ]}
    cx={120}
    cy={130}           {/* center at bottom of view = semicircle */}
    startAngle={180}
    endAngle={0}
    innerRadius={80}
    outerRadius={110}
    stroke="none"
    dataKey="value"
  >
    <Cell fill={gaugeColor(score)} />
    <Cell fill="var(--color-bg-sunken)" />
  </Pie>
</PieChart>
```

`gaugeColor(score)` returns:
- `#22C55E` if score ≥ 70
- `#F59E0B` if score 40–69
- `#EF4444` if score < 40

The score number is **absolutely positioned** over the center of the arc using CSS. `font-size: var(--text-4xl)`, `font-family: var(--font-family-mono)`, `font-weight: 600`, `letter-spacing: var(--letter-spacing-tight)`. Color matches `gaugeColor(score)`.

Tick marks around the arc: rendered as SVG lines at the 0, 40, 70, and 100 positions with labels "0", "40", "70", "100" in `text-xs text-tertiary`.

### 6.3 Sparkline (KPI Micro-chart)

Shared `TinySparkLine` component used in all 4 KPI cards.

```tsx
<ResponsiveContainer width={80} height={32}>
  <AreaChart data={data}>
    <Area
      type="monotone"
      dataKey="value"
      stroke={color}           {/* passed as prop */}
      strokeWidth={1.5}
      fill={`url(#spark-${id})`}
      dot={false}
      isAnimationActive={false}  {/* no animation on sparklines — they update too frequently */}
    />
  </AreaChart>
</ResponsiveContainer>
```

No axes, no grid, no tooltip. The gradient `id` must be unique per card instance (use a `useId()` hook) to avoid SVG gradient leakage.

### 6.4 Health Score History Line Chart

Full-width, used on the History page. 12-month line chart.

Single series: Health Score over time. Line color: dynamically colored — segments below 40 are red, 40-70 are amber, above 70 are green. This requires splitting the data into segments and rendering multiple `<Line>` series or using a custom `linearGradient` on the SVG.

**Recommended approach:** Render as a single `<Line>` but color the area under the line using three stacked semi-transparent `<Area>` components with fill thresholds for the three zones, using Recharts' `<ReferenceLine>` at y=40 and y=70 with `stroke="var(--color-border-subtle)"`, dashed.

Y-axis range: 0–100, explicitly set `domain={[0, 100]}`. Reference areas: `<ReferenceArea y1={0} y2={40} fill="rgba(239,68,68,0.04)" />`, `<ReferenceArea y1={40} y2={70} fill="rgba(245,158,11,0.04)" />`, `<ReferenceArea y1={70} y2={100} fill="rgba(34,197,94,0.04)" />`.

---

## 7. Component Library Catalogue

Every component listed here lives in `src/components/ui/`.

**`Button`** — CVA-driven with variants `intent: "primary" | "ghost" | "danger" | "outline"` and `size: "sm" | "md" | "lg"`. All buttons have `transition-all duration-150`, `focus-visible:ring-2 focus-visible:ring-primary-500`, `disabled:opacity-40 disabled:cursor-not-allowed`. Primary: `bg-primary-600 hover:bg-primary-500 text-white`. Ghost: `bg-transparent hover:bg-bg-hover text-secondary hover:text-primary`. Danger: `bg-danger-subtle hover:bg-danger-muted text-danger-bright`. Outline: `border border-border-default hover:border-border-strong bg-transparent text-primary`.

**`Badge` / `AlertBadge`** — CVA-driven, documented in section 5.1. Always uppercase, `letter-spacing: var(--letter-spacing-wider)`.

**`Card`** — A simple wrapper `div` with `bg-bg-raised border border-border-subtle rounded-lg shadow-md`. Accepts `className` for overrides. Inner `CardHeader`, `CardBody`, `CardFooter` sub-components for consistent padding.

**`Input`** — Wraps a `<input>` with the standard border, background, focus ring described in Settings. Accepts `leftIcon`, `rightIcon` props that add icon elements inside the input with appropriate padding adjustments.

**`Select`** — Wraps Radix UI `Select.Root`. Custom trigger styled to match `Input`. Popover: `bg-bg-elevated border border-border-default rounded-lg shadow-lg overflow-hidden`. Each item: `padding: 8px 12px`, `text-sm`, hover `bg-bg-hover`. Selected item has a `Check` icon on the right.

**`Switch`** — Wraps Radix UI `Switch.Root`. Documented in Settings section.

**`Avatar`** — `width: 32px`, `height: 32px`, `border-radius: full`. Shows image if available; falls back to initials. Background uses a deterministic color from the user's name hash (one of 6 muted brand colors).

**`Tooltip`** — Wraps Radix UI `Tooltip`. Content: `bg-bg-elevated border border-border-default text-xs rounded-md px-2 py-1 shadow-lg`. Delay: 400ms open, 0ms close. Max width: 240px.

**`SkeletonLoader`** — Documented in Section 3.6. Variants render differently shaped placeholder layouts: `"kpi-grid"` renders a 4-column grid of card-shaped skeletons; `"chart"` renders a tall rectangle; `"list"` renders 3 list-item rows; `"table"` renders a table with header and 5 rows.

---

## 8. Accessibility & Responsiveness

**ARIA requirements:** All icon-only buttons must have `aria-label`. The nav sidebar must have `role="navigation"` and `aria-label="Main navigation"`. The alert list must have `role="list"`. Each alert item must have `role="listitem"`. The chat message feed must have `role="log"` and `aria-live="polite"`. The upload drag zone must have `role="button"`, `aria-label="Upload CSV file"`, and be keyboard-activatable via `Enter`/`Space`.

**Keyboard navigation:** Tab order must follow visual order. The sidebar nav items must be fully keyboard navigable. The chat input must auto-focus on page mount. Modal dialogs must trap focus within themselves and restore focus to the trigger element on close.

**Contrast ratios:** All text must meet WCAG AA minimum (4.5:1 for normal text, 3:1 for large text). The color pairs defined in the design system have been validated: `--color-text-primary` on `--color-bg-raised` = 12.4:1. `--color-success-bright` on `--color-success-subtle` = 5.8:1.

**Responsive breakpoints (Tailwind):**
- `sm`: 640px — mobile landscape.
- `md`: 768px — tablet. Sidebar becomes a drawer.
- `lg`: 1024px — small laptop. KPI grid goes from 2 to 4 columns.
- `xl`: 1280px — desktop. Full layout with sidebar visible.
- `2xl`: 1536px — wide desktop. Max content width: `1400px`, centered.

The max content width wrapper: `max-w-[1400px] mx-auto`. This prevents layouts from becoming unreadably wide on large monitors.

---

## 9. Performance Budget

**Bundle size targets:**
- Initial JS (gzipped): <150KB.
- Recharts is lazy-loaded — it is only imported in chart components which are code-split by page using React Router's lazy loading.
- `react-markdown` + `remark-gfm`: lazy-loaded, only mounted in the Chat view.

**Rendering targets:**
- Time to First Contentful Paint (FCP): <1.2s on 4G.
- Largest Contentful Paint (LCP): <2.5s.
- No Cumulative Layout Shift (CLS) from font loading — use `font-display: swap` and reserve space with `min-height` on number display areas.
- KPI card numbers: reserve their character width to prevent reflow when data loads (use `ch` units for skeleton widths: `width: 8ch` for currency values).

**Image optimization:** The only images are user avatars (served with Next-gen formats, max 64px × 64px). All icons are inline SVG via Lucide React (tree-shaken).

**WebSocket:** Only one WebSocket connection, owned at the `AppShell` level. No per-component WebSocket connections.

---

## 10. Implementation Sequencing

Build CashPilot in this exact order to minimize rework and ensure a testable product at each stage.

**Phase 1 — Design System Foundation (Days 1–2):**
Implement `globals.css` with all CSS custom properties. Build and test all `src/components/ui/` primitives (Button, Badge, Card, Input, Select, Switch, Avatar, Tooltip, SkeletonLoader). No page code yet — just a Storybook or test page showing every component in every state.

**Phase 2 — Application Shell (Day 3):**
Build the Sidebar, Topbar, AppShell layout, theme toggle, and the Data Upload Modal. Wire up `AppContext` and `AlertsContext`. Wire up `useWebSocket` with console.log handlers for now.

**Phase 3 — Snapshot Page (Days 4–5):**
Build all chart components first (`TinySparkLine`, `HealthScoreGauge`, `RevenueExpenseChart`). Then build `KPICard` and `QuickStats`. Then `AnomalyWidget`. Wire up `useSnapshotData` with mock data initially, then swap to the real API endpoint.

**Phase 4 — Chat Page (Days 6–7):**
Build `ChatInput`, `MessageBubble`, `TypingIndicator`, `ToolCallPill`, `MessageFeed`. Wire up `useChatSession`. Test the full conversation loop with mock responses, then wire up the real `POST /api/v1/chat`.

**Phase 5 — Alerts & History Pages (Days 8–9):**
Alerts first (simpler). Build `AlertItem`, `AlertList`, `AlertFilters`. Wire real API with React Query. Then History page: `HealthScoreHistory` chart and `DataRunsTable` with pagination.

**Phase 6 — Settings & Polish (Day 10):**
Settings forms. Then: audit all pages for responsiveness, verify all skeleton loaders and error states, test keyboard navigation, and validate color contrast. Final round of animation polish.

---

*This document is the single source of truth for CashPilot frontend implementation. Any deviation from these specifications — particularly from the color semantic system or the component modularity rules — must be explicitly justified and reviewed.*
