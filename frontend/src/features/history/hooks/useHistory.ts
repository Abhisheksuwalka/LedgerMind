import { apiFetch } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

export interface RunReport {
  report_id: string;
  executive_summary: string;
  period_start: string | null;
  period_end: string | null;
}

export interface HistoryRun {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
  summary: string | null;
  report: RunReport | null;
}

export interface HealthScorePoint {
  date: string;
  score: number;
}

export function useHistory() {
  return useQuery<HistoryRun[]>({
    queryKey: ['history'],
    queryFn: () => apiFetch<HistoryRun[]>('/history'),
    staleTime: 30_000,
    refetchInterval: 15_000,
  });
}
