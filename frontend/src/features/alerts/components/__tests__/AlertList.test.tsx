/**
 * Property tests for AlertList component.
 *
 * Property 1: Alert list count matches input
 * For any array of Alert objects passed to AlertList, the number of rendered
 * AlertItem elements equals the length of the input array.
 *
 * Validates: Requirement 2.3
 */

import type { Alert } from '@/types/alert';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { describe, expect, it, vi } from 'vitest';
import { AlertList } from '../AlertList';

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

const noop = vi.fn();

// ---------------------------------------------------------------------------
// Property 1: Alert list count matches input
// ---------------------------------------------------------------------------

describe('Property 1: Alert list count matches input', () => {
  it('renders exactly one AlertItem per alert in the input array', () => {
    fc.assert(
      fc.property(fc.array(alertArb, { minLength: 1, maxLength: 30 }), (alerts) => {
        // Ensure unique ids to avoid React key warnings affecting count
        const uniqueAlerts = alerts.map((a, i) => ({ ...a, id: String(i) }));

        const { unmount } = render(
          <AlertList
            alerts={uniqueAlerts}
            isLoading={false}
            onMarkRead={noop}
            onDismiss={noop}
          />
        );

        const items = screen.getAllByTestId('alert-item');
        expect(items).toHaveLength(uniqueAlerts.length);

        unmount();
      }),
      { numRuns: 100 }
    );
  });

  it('renders empty state when alerts array is empty', () => {
    const { unmount } = render(
      <AlertList alerts={[]} isLoading={false} onMarkRead={noop} onDismiss={noop} />
    );

    expect(screen.getByText('No alerts to display.')).toBeTruthy();
    expect(screen.queryAllByTestId('alert-item')).toHaveLength(0);

    unmount();
  });

  it('renders skeleton when isLoading is true', () => {
    const { unmount } = render(
      <AlertList alerts={[]} isLoading={true} onMarkRead={noop} onDismiss={noop} />
    );

    expect(screen.queryAllByTestId('alert-item')).toHaveLength(0);

    unmount();
  });
});
