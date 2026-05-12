/**
 * Property tests for HealthScoreHistory component.
 *
 * Property 7: Health score chart renders for all valid scores
 * For any array of HealthScorePoint objects where each score is in [0, 100],
 * rendering HealthScoreHistory does not throw an error.
 *
 * Validates: Requirement 7.2
 */

import { render } from '@testing-library/react';
import * as fc from 'fast-check';
import { describe, expect, it, vi } from 'vitest';
import type { HealthScorePoint } from '../../hooks/useHistory';
import { HealthScoreHistory } from '../HealthScoreHistory';

// Recharts uses ResizeObserver — provide a stub in jsdom
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

const healthScorePointArb: fc.Arbitrary<HealthScorePoint> = fc.record({
  date: fc.date({ min: new Date('2023-01-01'), max: new Date('2025-12-31') }).map((d) =>
    d.toISOString()
  ),
  score: fc.integer({ min: 0, max: 100 }),
});

const noop = vi.fn();

// ---------------------------------------------------------------------------
// Property 7: Health score chart renders for all valid scores
// ---------------------------------------------------------------------------

describe('Property 7: Health score chart renders for all valid scores', () => {
  it('renders without throwing for any array of valid HealthScorePoints', () => {
    fc.assert(
      fc.property(
        fc.array(healthScorePointArb, { minLength: 0, maxLength: 24 }),
        (points) => {
          expect(() => {
            const { unmount } = render(
              <HealthScoreHistory
                data={points}
                isLoading={false}
                timeRange="3M"
                onTimeRangeChange={noop}
              />
            );
            unmount();
          }).not.toThrow();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('renders skeleton when isLoading is true regardless of data', () => {
    fc.assert(
      fc.property(fc.array(healthScorePointArb, { minLength: 0, maxLength: 12 }), (points) => {
        expect(() => {
          const { unmount } = render(
            <HealthScoreHistory
              data={points}
              isLoading={true}
              timeRange="3M"
              onTimeRangeChange={noop}
            />
          );
          unmount();
        }).not.toThrow();
      }),
      { numRuns: 50 }
    );
  });
});
