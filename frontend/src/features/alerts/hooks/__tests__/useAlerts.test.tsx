/**
 * Property-based tests for useAlerts mutations and AlertsContext synchronisation.
 *
 * **Validates: Requirements 5.4 (Property 5) and 5.2 (Property 6)**
 */

import { AlertsContextProvider, useAlertsContext } from '@/store/AlertsContext';
import type { Alert } from '@/types/alert';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import * as fc from 'fast-check';
import React from 'react';
import { describe, expect, it } from 'vitest';
import { useMarkAlertRead, useMarkAllRead } from '../useAlerts';

// ---------------------------------------------------------------------------
// Arbitraries
// ---------------------------------------------------------------------------

const severityArb = fc.constantFrom<Alert['severity']>('info', 'warning', 'critical');

const alertArb: fc.Arbitrary<Alert> = fc.record({
  id: fc.uuid(),
  title: fc.string({ minLength: 1, maxLength: 80 }),
  description: fc.string({ minLength: 0, maxLength: 200 }),
  severity: severityArb,
  isRead: fc.boolean(),
  createdAt: fc
    .date({ min: new Date('2020-01-01'), max: new Date('2030-01-01') })
    .map((d) => d.toISOString()),
});

/** At least one unread alert */
const alertArrayWithUnreadArb = fc
  .array(alertArb, { minLength: 1, maxLength: 20 })
  .filter((alerts) => alerts.some((a) => !a.isRead));

// ---------------------------------------------------------------------------
// Wrapper factory — fresh QueryClient per test to avoid cache bleed
// ---------------------------------------------------------------------------

function makeWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AlertsContextProvider>{children}</AlertsContextProvider>
      </QueryClientProvider>
    );
  };
}

// ---------------------------------------------------------------------------
// Property 5: Mark-all-read sets unread count to zero
//
// For any array of Alert objects, after useMarkAllRead is called,
// AlertsContext.unreadCount equals 0.
//
// **Validates: Requirement 5.4**
// ---------------------------------------------------------------------------

describe('Property 5: Mark-all-read sets unread count to zero', () => {
  it(
    'unreadCount is 0 after useMarkAllRead succeeds',
    async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.array(alertArb, { minLength: 0, maxLength: 20 }),
          async (alerts) => {
            const queryClient = new QueryClient({
              defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
            });
            const wrapper = makeWrapper(queryClient);

            const { result } = renderHook(
              () => ({
                ctx: useAlertsContext(),
                markAllRead: useMarkAllRead(),
              }),
              { wrapper }
            );

            // Seed the context with the current unread count
            const initialUnread = alerts.filter((a) => !a.isRead).length;
            act(() => {
              result.current.ctx.setUnreadCount(initialUnread);
            });

            expect(result.current.ctx.unreadCount).toBe(initialUnread);

            // Call markAllRead
            await act(async () => {
              result.current.markAllRead.mutate();
            });

            await waitFor(
              () => {
                expect(result.current.markAllRead.isSuccess).toBe(true);
              },
              { timeout: 3000 }
            );

            // After success, unreadCount must be 0
            expect(result.current.ctx.unreadCount).toBe(0);
          }
        ),
        { numRuns: 10 }
      );
    },
    30_000
  );
});

// ---------------------------------------------------------------------------
// Property 6: Mark-read decrements unread count by one
//
// For any alert list containing at least one unread alert, after
// useMarkAlertRead succeeds for one alert, AlertsContext.unreadCount
// decreases by exactly 1.
//
// **Validates: Requirement 5.2**
// ---------------------------------------------------------------------------

describe('Property 6: Mark-read decrements unread count by one', () => {
  it(
    'unreadCount decreases by exactly 1 after useMarkAlertRead succeeds',
    async () => {
      await fc.assert(
        fc.asyncProperty(alertArrayWithUnreadArb, async (alerts) => {
          const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
          });
          const wrapper = makeWrapper(queryClient);

          const { result } = renderHook(
            () => ({
              ctx: useAlertsContext(),
              markRead: useMarkAlertRead(),
            }),
            { wrapper }
          );

          // Seed the context with the current unread count
          const initialUnread = alerts.filter((a) => !a.isRead).length;
          act(() => {
            result.current.ctx.setUnreadCount(initialUnread);
          });

          expect(result.current.ctx.unreadCount).toBe(initialUnread);

          // Use alert id '1' which always exists in MOCK_ALERTS
          await act(async () => {
            result.current.markRead.mutate('1');
          });

          await waitFor(
            () => {
              expect(result.current.markRead.isSuccess).toBe(true);
            },
            { timeout: 3000 }
          );

          // unreadCount must have decreased by exactly 1 (floor at 0)
          expect(result.current.ctx.unreadCount).toBe(Math.max(0, initialUnread - 1));
        }),
        { numRuns: 10 }
      );
    },
    30_000
  );
});
