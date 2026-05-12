import { SkeletonLoader } from '@/components/ui/SkeletonLoader';
import { useUploadModal } from '@/hooks/useUploadModal';
import { cn } from '@/lib/cn';
import { formatRelativeTime } from '@/lib/formatters';
import { AlertCircle, RefreshCw, Upload } from 'lucide-react';
import { useState } from 'react';
import { AnomalyWidget } from './components/AnomalyWidget';
import { HealthScoreGauge } from './components/HealthScoreGauge';
import { QuickStats } from './components/QuickStats';
import { RevenueExpenseChart } from './components/RevenueExpenseChart';
import { useSnapshotData } from './hooks/useSnapshotData';

const TIME_RANGE_OPTIONS = ['3M', '6M', '12M'] as const;
type TimeRange = (typeof TIME_RANGE_OPTIONS)[number];

interface PageHeaderProps {
  title: string;
  lastSyncedAt?: string | null;
  onRefresh: () => void;
  isRefreshing: boolean;
  timeRange: TimeRange;
  onTimeRangeChange: (r: TimeRange) => void;
}

function PageHeader({ title, lastSyncedAt, onRefresh, isRefreshing, timeRange, onTimeRangeChange }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-primary">{title}</h1>
        {lastSyncedAt ? (
          <p className="text-sm text-secondary mt-1">
            Last synced: {formatRelativeTime(lastSyncedAt)}
          </p>
        ) : (
          <p className="text-sm text-tertiary mt-1">No data uploaded yet</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Period selector */}
        <div className="flex items-center bg-bg-raised border border-border-subtle rounded-lg overflow-hidden">
          {TIME_RANGE_OPTIONS.map((r) => (
            <button
              key={r}
              onClick={() => onTimeRangeChange(r)}
              className={cn(
                'px-3 py-1.5 text-xs font-semibold transition-colors',
                timeRange === r
                  ? 'bg-primary-700 text-white'
                  : 'text-secondary hover:text-primary hover:bg-bg-hover'
              )}
            >
              {r}
            </button>
          ))}
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 text-secondary hover:text-primary transition-colors disabled:opacity-50"
          aria-label="Refresh data"
        >
          <RefreshCw size={18} className={isRefreshing ? 'animate-spin' : 'hover:rotate-180 transition-transform duration-500 ease-in-out'} />
        </button>
      </div>
    </div>
  );
}

function FeatureBoundary({
  isLoading,
  variant,
  className,
  children
}: {
  isLoading: boolean;
  variant: any;
  className?: string;
  children: React.ReactNode;
}) {
  if (isLoading) {
    return <SkeletonLoader variant={variant} className={className} />;
  }
  return <div className={className}>{children}</div>;
}

function EmptyState({ onUpload }: { onUpload: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-6 text-center">
      <div className="p-5 rounded-full bg-bg-elevated border border-border-default">
        <Upload size={32} className="text-tertiary" />
      </div>
      <div className="max-w-sm">
        <p className="text-lg font-semibold text-primary">No financial data yet</p>
        <p className="text-sm text-secondary mt-2">
          Upload a CSV or JSON file to see your financial snapshot, anomalies, and cash runway.
        </p>
      </div>
      <button
        onClick={onUpload}
        className="px-5 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-colors flex items-center gap-2"
      >
        <Upload size={16} />
        Upload Financial Data
      </button>
    </div>
  );
}

function BackendError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      <div className="p-4 rounded-full bg-red-900/20 border border-red-700/40">
        <AlertCircle size={28} className="text-red-400" />
      </div>
      <div className="max-w-sm">
        <p className="text-primary font-medium">Could not reach the backend</p>
        <p className="text-secondary text-sm mt-2">
          Make sure the backend server is running at{' '}
          <code className="text-xs bg-bg-raised px-1 py-0.5 rounded">
            {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
          </code>
        </p>
      </div>
      <button
        onClick={onRetry}
        className="px-4 py-2 rounded-lg border border-border-default text-secondary hover:text-primary hover:border-border-strong transition-colors text-sm flex items-center gap-2"
      >
        <RefreshCw size={14} />
        Retry
      </button>
    </div>
  );
}

export default function Snapshot() {
  const [timeRange, setTimeRange] = useState<TimeRange>('12M');
  const { data, isLoading, isError, refetch, isFetching } = useSnapshotData(timeRange);
  const { openModal } = useUploadModal();

  // Determine if we genuinely have no data (backend returned empty snapshot)
  const hasData = Boolean(
    data && (data.chartData.length > 0 || data.quickStats.totalRevenue.value > 0)
  );

  return (
    <main className="p-4 sm:p-8 space-y-8 max-w-[1400px] mx-auto">
      <PageHeader
        title="Financial Snapshot"
        lastSyncedAt={data?.lastSyncedAt}
        onRefresh={refetch}
        isRefreshing={isFetching}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
      />

      {/* Backend unreachable */}
      {isError && !isLoading && (
        <BackendError onRetry={refetch} />
      )}

      {/* No data yet — show upload prompt */}
      {!isLoading && !isError && !hasData && (
        <EmptyState onUpload={openModal} />
      )}

      {/* Data available */}
      {!isError && (hasData || isLoading) && (
        <>
          <FeatureBoundary isLoading={isLoading} variant="kpi-grid">
            {data && <QuickStats data={data.quickStats} />}
          </FeatureBoundary>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <FeatureBoundary isLoading={isLoading} variant="chart" className="xl:col-span-2">
              {data && <RevenueExpenseChart data={data.chartData} />}
            </FeatureBoundary>

            <FeatureBoundary isLoading={isLoading} variant="chart">
              {data && <HealthScoreGauge score={data.healthScore} />}
            </FeatureBoundary>
          </div>

          <FeatureBoundary isLoading={isLoading} variant="list">
            {data && <AnomalyWidget anomalies={data.anomalies} />}
          </FeatureBoundary>
        </>
      )}
    </main>
  );
}
