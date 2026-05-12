import { useHistory, type HistoryRun } from './hooks/useHistory';
import { cn } from '@/lib/cn';
import { CheckCircle, AlertCircle, Loader2, Clock, FileText, Upload } from 'lucide-react';

const STATUS_CONFIG = {
  completed: {
    icon: CheckCircle,
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10 border-emerald-400/20',
    label: 'Completed',
  },
  failed: {
    icon: AlertCircle,
    color: 'text-red-400',
    bg: 'bg-red-400/10 border-red-400/20',
    label: 'Failed',
  },
  running: {
    icon: Loader2,
    color: 'text-blue-400',
    bg: 'bg-blue-400/10 border-blue-400/20',
    label: 'Running',
  },
  pending: {
    icon: Clock,
    color: 'text-slate-400',
    bg: 'bg-slate-400/10 border-slate-400/20',
    label: 'Pending',
  },
};

function formatDuration(started: string, completed: string | null): string {
  if (!completed) return '—';
  const ms = new Date(completed).getTime() - new Date(started).getTime();
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function RunCard({ run }: { run: HistoryRun }) {
  const cfg = STATUS_CONFIG[run.status] ?? STATUS_CONFIG.pending;
  const Icon = cfg.icon;
  const isRunning = run.status === 'running';

  return (
    <div className="bg-bg-elevated border border-border-default rounded-xl p-5 space-y-4 hover:border-border-strong transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className={cn('p-1.5 rounded-lg border', cfg.bg)}>
            <Icon size={16} className={cn(cfg.color, isRunning && 'animate-spin')} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-primary truncate">
              {run.triggered_by === 'manual' ? 'Manual Upload' : run.triggered_by}
            </p>
            <p className="text-xs text-tertiary mt-0.5">{formatDate(run.started_at)}</p>
          </div>
        </div>

        <span className={cn(
          'shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full border',
          cfg.bg, cfg.color
        )}>
          {cfg.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-bg-sunken rounded-lg p-3">
          <p className="text-tertiary">Duration</p>
          <p className="text-secondary font-mono mt-0.5">{formatDuration(run.started_at, run.completed_at)}</p>
        </div>
        <div className="bg-bg-sunken rounded-lg p-3">
          <p className="text-tertiary">Run ID</p>
          <p className="text-secondary font-mono mt-0.5 truncate" title={run.run_id}>
            {run.run_id.substring(0, 8)}…
          </p>
        </div>
      </div>

      {run.report && run.report.executive_summary && (
        <div className="border-t border-border-subtle pt-3">
          <div className="flex items-center gap-1.5 mb-2">
            <FileText size={12} className="text-tertiary" />
            <p className="text-xs font-medium text-tertiary uppercase tracking-wide">Summary</p>
          </div>
          <p className="text-sm text-secondary leading-relaxed line-clamp-3">
            {run.report.executive_summary}
          </p>
        </div>
      )}
    </div>
  );
}

export default function History() {
  const { data: runs, isLoading, error } = useHistory();

  return (
    <main className="p-4 md:p-8 space-y-6 max-w-[1000px] mx-auto w-full pb-20">
      <header>
        <h1 className="text-2xl font-bold text-primary">Analysis History</h1>
        <p className="text-sm text-secondary mt-1">
          All pipeline runs — each card shows the run status, duration, and executive summary.
        </p>
      </header>

      {isLoading && (
        <div className="flex items-center gap-3 text-secondary">
          <Loader2 size={18} className="animate-spin" />
          <span className="text-sm">Loading history…</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-900/20 border border-red-700/40 rounded-xl text-sm text-red-300">
          <AlertCircle size={18} />
          Could not load history. Is the backend running?
        </div>
      )}

      {!isLoading && !error && (!runs || runs.length === 0) && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <div className="p-4 rounded-full bg-bg-elevated border border-border-default">
            <Upload size={24} className="text-tertiary" />
          </div>
          <div>
            <p className="text-primary font-medium">No analysis runs yet</p>
            <p className="text-secondary text-sm mt-1">
              Upload a CSV or JSON file to run your first financial analysis.
            </p>
          </div>
        </div>
      )}

      {runs && runs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {runs.map((run) => (
            <RunCard key={run.run_id} run={run} />
          ))}
        </div>
      )}
    </main>
  );
}
