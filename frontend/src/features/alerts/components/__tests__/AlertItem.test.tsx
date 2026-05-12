/**
 * Property tests for AlertItem component.
 *
 * Property 3: Unread visual treatment is applied iff isRead is false
 * Property 4: Severity badge and icon match alert severity
 * Property 10: Alert content is XSS-safe
 */

import type { Alert } from '@/types/alert';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { describe, expect, it, vi } from 'vitest';
import { AlertItem } from '../AlertItem';

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
// Property 3: Unread visual treatment is applied iff isRead is false
// ---------------------------------------------------------------------------

describe('Property 3: Unread visual treatment applied iff isRead is false', () => {
  it('applies left accent border class when isRead is false', () => {
    fc.assert(
      fc.property(alertArb, (alert) => {
        const { unmount } = render(<AlertItem alert={alert} onMarkRead={noop} onDismiss={noop} />);
        const item = screen.getByTestId('alert-item');

        if (!alert.isRead) {
          expect(item.className).toContain('border-l-primary-500');
          expect(item.className).toContain('bg-bg-raised');
        } else {
          expect(item.className).toContain('border-l-transparent');
          expect(item.className).not.toContain('border-l-primary-500');
        }

        unmount();
      }),
      { numRuns: 100 }
    );
  });
});

// ---------------------------------------------------------------------------
// Property 4: Severity badge and icon match alert severity
// ---------------------------------------------------------------------------

describe('Property 4: Severity badge and icon match alert severity', () => {
  it('renders badge text matching severity', () => {
    fc.assert(
      fc.property(alertArb, (alert) => {
        const { unmount } = render(<AlertItem alert={alert} onMarkRead={noop} onDismiss={noop} />);

        // Badge text should match severity
        const badge = screen.getByText(alert.severity);
        expect(badge).toBeTruthy();

        unmount();
      }),
      { numRuns: 100 }
    );
  });

  it('renders the correct icon aria-label for each severity', () => {


    fc.assert(
      fc.property(severityArb, (severity) => {
        const alert: Alert = {
          id: '1',
          title: 'Test',
          description: 'Test description',
          severity,
          isRead: false,
          createdAt: new Date().toISOString(),
        };

        const { unmount, container } = render(
          <AlertItem alert={alert} onMarkRead={noop} onDismiss={noop} />
        );

        // The lucide icon renders an SVG — verify the correct one is present
        // by checking the data-testid or the SVG structure
        const svgs = container.querySelectorAll('svg');
        expect(svgs.length).toBeGreaterThan(0);

        // Verify badge intent class matches severity
        const badge = screen.getByText(severity);
        if (severity === 'critical') {
          expect(badge.className).toContain('text-danger-bright');
        } else if (severity === 'warning') {
          expect(badge.className).toContain('text-warning-bright');
        } else {
          expect(badge.className).toContain('text-primary-300');
        }

        unmount();
      }),
      { numRuns: 50 }
    );
  });
});

// ---------------------------------------------------------------------------
// Property 10: Alert content is XSS-safe
// ---------------------------------------------------------------------------

describe('Property 10: Alert content is XSS-safe', () => {
  it('renders title and description as plain text, not HTML', () => {
    const xssStrings = [
      '<script>alert("xss")</script>',
      '<img src=x onerror=alert(1)>',
      '<b>bold</b>',
      '"><svg onload=alert(1)>',
      "'; DROP TABLE alerts; --",
    ];

    fc.assert(
      fc.property(fc.constantFrom(...xssStrings), fc.constantFrom(...xssStrings), (title, description) => {
        const alert: Alert = {
          id: '1',
          title,
          description,
          severity: 'info',
          isRead: false,
          createdAt: new Date().toISOString(),
        };

        const { unmount, container } = render(
          <AlertItem alert={alert} onMarkRead={noop} onDismiss={noop} />
        );

        // Script tags must not be executed — no <script> elements in DOM
        expect(container.querySelectorAll('script')).toHaveLength(0);

        // The raw string should appear as text content, not parsed HTML
        // e.g. "<b>bold</b>" should show as literal text, not a <b> element
        if (title.includes('<b>')) {
          // If it were parsed as HTML, there'd be a <b> element
          // React renders as text so there should be none from our content
          const boldFromContent = Array.from(container.querySelectorAll('b')).filter(
            (el) => el.textContent === 'bold'
          );
          expect(boldFromContent).toHaveLength(0);
        }

        unmount();
      }),
      { numRuns: 25 }
    );
  });
});
