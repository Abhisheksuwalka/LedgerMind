import { useAlertsContext } from '@/store/AlertsContext';
import type { Alert } from '@/types/alert';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '@/lib/api';

// ---------------------------------------------------------------------------
// Shape returned by the backend /alerts endpoint
// ---------------------------------------------------------------------------

interface BackendAlert {
  id: string;
  title: string;
  message: string;
  alert_type: string;
  severity: string;
  is_read: boolean;
  created_at: string;
}

/** Map backend snake_case alert → frontend camelCase Alert */
function mapAlert(a: BackendAlert): Alert {
  return {
    id: a.id,
    title: a.title,
    description: a.message,
    severity: (a.severity === 'critical' ? 'critical' : a.severity === 'high' ? 'critical' : a.severity === 'low' ? 'info' : 'warning') as Alert['severity'],
    isRead: a.is_read,
    createdAt: a.created_at,
  };
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

export function useAlerts(filters: { severity: string; sort: string }) {
  return useQuery<Alert[]>({
    queryKey: ['alerts', filters],
    queryFn: async () => {
      const raw = await apiFetch<BackendAlert[]>('/alerts');
      let results = raw.map(mapAlert);

      if (filters.severity !== 'all') {
        results = results.filter((a) => a.severity === filters.severity);
      }

      if (filters.sort === 'oldest') {
        results = results.sort(
          (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
        );
      } else if (filters.sort === 'severity') {
        const order: Record<Alert['severity'], number> = { critical: 0, warning: 1, info: 2 };
        results = results.sort((a, b) => order[a.severity] - order[b.severity]);
      } else {
        // default: newest first
        results = results.sort(
          (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
      }

      return results;
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useMarkAlertRead() {
  const queryClient = useQueryClient();
  const { decrementUnread } = useAlertsContext();

  return useMutation<Alert, Error, string>({
    mutationFn: async (alertId: string) => {
      await apiFetch(`/alerts/${alertId}/read`, { method: 'PATCH' });
      return { id: alertId, isRead: true } as unknown as Alert;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      decrementUnread();
    },
  });
}

export function useDismissAlert() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (alertId: string) => {
      await apiFetch(`/alerts/${alertId}`, { method: 'DELETE' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  const { setToZero } = useAlertsContext();

  return useMutation<void, Error, void>({
    mutationFn: async () => {
      // Fetch current unread alerts and mark them all read in parallel
      const raw = await apiFetch<BackendAlert[]>('/alerts');
      const unread = raw.filter((a) => !a.is_read);
      await Promise.all(
        unread.map((a) => apiFetch(`/alerts/${a.id}/read`, { method: 'PATCH' }).catch(() => {}))
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      setToZero();
    },
  });
}
