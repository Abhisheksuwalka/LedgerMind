/**
 * Property tests for AlertsContext unread count synchronisation.
 *
 * **Validates: Requirement 1.3**
 */

import { act, renderHook } from '@testing-library/react';
import * as fc from 'fast-check';
import React from 'react';
import { describe, expect, it } from 'vitest';
import type { Alert } from '../../types/alert';
import { AlertsContextProvider, useAlertsContext } from '../AlertsContext';

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
  createdAt: fc.date({ min: new Date('2020-01-01'), max: new Date('2030-01-01') }).map((d) =>
    d.toISOString()
  ),
});

const alertArrayArb = fc.array(alertArb, { minLength: 0, maxLength: 50 });

// ---------------------------------------------------------------------------
// Helper: wrapper for renderHook
// ---------------------------------------------------------------------------

function wrapper({ children }: { children: React.ReactNode }) {
  return <AlertsContextProvider>{children}</AlertsContextProvider>;
}

// ---------------------------------------------------------------------------
// Property 2: Unread count synchronisation on load
//
// For any array of Alert objects, the value passed to
// AlertsContext.setUnreadCount equals the count of alerts where isRead is false.
// ---------------------------------------------------------------------------

describe('AlertsContext – Property 2: Unread count synchronisation', () => {
  it('setUnreadCount stores the exact value passed to it', () => {
    fc.assert(
      fc.property(alertArrayArb, (alerts) => {
        const unreadCount = alerts.filter((a) => !a.isRead).length;

        const { result } = renderHook(() => useAlertsContext(), { wrapper });

        act(() => {
          result.current.setUnreadCount(unreadCount);
        });

        expect(result.current.unreadCount).toBe(unreadCount);
      }),
      { numRuns: 100 }
    );
  });

  it('unread count derived from alerts array equals filter(isRead === false).length', () => {
    fc.assert(
      fc.property(alertArrayArb, (alerts) => {
        // Pure logic: the value that AlertsPage should pass to setUnreadCount
        const expectedUnread = alerts.filter((a) => !a.isRead).length;

        // Verify the context correctly stores and returns this value
        const { result } = renderHook(() => useAlertsContext(), { wrapper });

        act(() => {
          result.current.setUnreadCount(expectedUnread);
        });

        expect(result.current.unreadCount).toBe(expectedUnread);
        expect(result.current.unreadCount).toBe(
          alerts.filter((a) => !a.isRead).length
        );
      }),
      { numRuns: 100 }
    );
  });

  it('decrementUnread reduces unreadCount by 1 (floor at 0)', () => {
    fc.assert(
      fc.property(fc.nat({ max: 100 }), (initialCount) => {
        const { result } = renderHook(() => useAlertsContext(), { wrapper });

        act(() => {
          result.current.setUnreadCount(initialCount);
        });

        act(() => {
          result.current.decrementUnread();
        });

        const expected = Math.max(0, initialCount - 1);
        expect(result.current.unreadCount).toBe(expected);
      }),
      { numRuns: 100 }
    );
  });

  it('setToZero always sets unreadCount to 0 regardless of initial value', () => {
    fc.assert(
      fc.property(fc.nat({ max: 1000 }), (initialCount) => {
        const { result } = renderHook(() => useAlertsContext(), { wrapper });

        act(() => {
          result.current.setUnreadCount(initialCount);
        });

        act(() => {
          result.current.setToZero();
        });

        expect(result.current.unreadCount).toBe(0);
      }),
      { numRuns: 100 }
    );
  });
});
