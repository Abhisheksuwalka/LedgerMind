import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { SkeletonLoader } from '@/components/ui/SkeletonLoader';
import { cn } from '@/lib/cn';
import { useMemo } from 'react';
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import type { HealthScorePoint } from '../hooks/useHistory';

const TIME_RANGES = ['1M', '3M', '6M', '12M', 'All'] as const;
type TimeRange = (typeof TIME_RANGES)[number];

interface HealthScoreHistoryProps {
  data: HealthScorePoint[];
  isLoading: boolean;
  isError?: boolean;
  timeRange: TimeRange;
  onTimeRangeChange: (range: TimeRange) => void;
  onRetry?: () => void;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
}

export function HealthScoreHistory({
  data,
  isLoading,
  isError,
  timeRange,
  onTimeRangeChange,
  onRetry,
}: HealthScoreHistoryProps) {
  const chartData = useMemo(
    () => data.map((p) => ({ ...p, date: formatDate(p.date) })),
    [data]
  );

  if (isLoading) {
    return <SkeletonLoader variant="chart" />;
  }

  if (isError) {
    return (
      <Card className="p-6 flex flex-col items-center gap-3 text-center">
        <p className="text-sm text-secondary">Failed to load health score history.</p>
        {onRetry && (
          <Button intent="outline" size="sm" onClick={onRetry}>
            Retry
          </Button>
        )}
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <h2 className="text-base font-semibold text-primary">Health Score History</h2>
        {/* Time-range toggle pills */}
        <div className="flex gap-1">
          {TIME_RANGES.map((range) => (
            <button
              key={range}
              onClick={() => onTimeRangeChange(range)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                timeRange === range
                  ? 'bg-primary-600 text-white'
                  : 'text-secondary hover:bg-bg-hover hover:text-primary'
              )}
            >
              {range}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardBody>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chartData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="healthScoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: '#0f172a',
                border: '1px solid #1e293b',
                borderRadius: 8,
              }}
              labelStyle={{ color: '#94a3b8' }}
              formatter={(value: number) => [value, 'Score']}
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#22c55e"
              strokeWidth={2}
              fill="url(#healthScoreGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  );
}
