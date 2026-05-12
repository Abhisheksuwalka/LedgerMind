import { apiFetch } from '@/lib/api';
import type { SnapshotData } from '@/types/snapshot';
import { useQuery } from '@tanstack/react-query';

export function useSnapshotData(_timeRange: string = '12M') {
  return useQuery<SnapshotData>({
    queryKey: ['snapshot'],
    // Let errors propagate so the UI can show a proper error state
    // instead of silently returning zeros.
    queryFn: () => apiFetch<SnapshotData>('/snapshot'),
    // Refresh every 30 seconds in case data changes after an upload
    refetchInterval: 30_000,
    staleTime: 10_000,
    // Don't retry aggressively — backend may be starting up
    retry: 2,
    retryDelay: 3000,
  });
}
