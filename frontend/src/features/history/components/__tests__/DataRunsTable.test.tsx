/**
 * Property tests for DataRunsTable component.
 *
 * Property 8: Pagination range label is always valid
 * Property 9: Status badge intent mapping is exhaustive
 *
 * Validates: Requirements 8.2, 8.3
 */

import type { DataRun } from '@/types/report';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { describe, expect, it, vi } from 'vitest';
import { DataRunsTable } from '../DataRunsTable';

const statusArb = fc.constantFrom<DataRun['status']>('Completed', 'Processing', 'Failed');



const noop = vi.fn();

// ---------------------------------------------------------------------------
// Property 8: Pagination range label is always valid
// ---------------------------------------------------------------------------

describe('Property 8: Pagination range label is always valid', () => {
  it('displays correct range label for any valid page/pageSize/total combination', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 100 }),  // pageSize
        fc.integer({ min: 1, max: 500 }),  // total
        (pageSize, total) => {
          const lastPage = Math.ceil(total / pageSize);
          // Pick a random valid page
          const page = Math.floor(Math.random() * lastPage) + 1;

          const rangeStart = (page - 1) * pageSize + 1;
          const rangeEnd = Math.min(page * pageSize, total);

          // Build enough mock runs for this page
          const runs: DataRun[] = Array.from({ length: rangeEnd - rangeStart + 1 }, (_, i) => ({
            id: String(i),
            status: 'Completed' as const,
            runDate: new Date().toISOString(),
            insights: 'Test insight',
          }));

          const { unmount } = render(
            <DataRunsTable
              runs={runs}
              total={total}
              page={page}
              pageSize={pageSize}
              isLoading={false}
              onPageChange={noop}
            />
          );

          const label = screen.getByText(`Showing ${rangeStart}–${rangeEnd} of ${total}`);
          expect(label).toBeTruthy();

          // Upper bound must never exceed total
          expect(rangeEnd).toBeLessThanOrEqual(total);
          // Lower bound must be at least 1
          expect(rangeStart).toBeGreaterThanOrEqual(1);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('disables Prev button on page 1', () => {
    const { unmount } = render(
      <DataRunsTable
        runs={[{ id: '1', status: 'Completed', runDate: new Date().toISOString(), insights: 'x' }]}
        total={10}
        page={1}
        pageSize={5}
        isLoading={false}
        onPageChange={noop}
      />
    );
    const prevBtn = screen.getByRole('button', { name: /prev/i });
    expect(prevBtn).toBeDisabled();
    unmount();
  });

  it('disables Next button on last page', () => {
    const { unmount } = render(
      <DataRunsTable
        runs={[{ id: '1', status: 'Completed', runDate: new Date().toISOString(), insights: 'x' }]}
        total={5}
        page={1}
        pageSize={5}
        isLoading={false}
        onPageChange={noop}
      />
    );
    const nextBtn = screen.getByRole('button', { name: /next/i });
    expect(nextBtn).toBeDisabled();
    unmount();
  });
});

// ---------------------------------------------------------------------------
// Property 9: Status badge intent mapping is exhaustive
// ---------------------------------------------------------------------------

describe('Property 9: Status badge intent mapping is exhaustive', () => {
  it('renders correct badge intent for every DataRun status', () => {
    fc.assert(
      fc.property(statusArb, (status) => {
        const run: DataRun = {
          id: '1',
          status,
          runDate: new Date().toISOString(),
          insights: 'Test',
        };

        const { unmount } = render(
          <DataRunsTable
            runs={[run]}
            total={1}
            page={1}
            pageSize={5}
            isLoading={false}
            onPageChange={noop}
          />
        );

        const badge = screen.getByText(status);

        if (status === 'Completed') {
          expect(badge.className).toContain('text-primary-300'); // info intent
        } else if (status === 'Processing') {
          expect(badge.className).toContain('text-warning-bright'); // warning intent
        } else if (status === 'Failed') {
          expect(badge.className).toContain('text-danger-bright'); // critical intent
        }

        unmount();
      }),
      { numRuns: 50 }
    );
  });
});
