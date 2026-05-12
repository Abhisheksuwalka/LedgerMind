import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { SkeletonLoader } from '@/components/ui/SkeletonLoader';
import type { DataRun } from '@/types/report';

const statusIntent: Record<DataRun['status'], 'info' | 'warning' | 'critical'> = {
  Completed: 'info',
  Processing: 'warning',
  Failed: 'critical',
};

interface DataRunsTableProps {
  runs: DataRun[];
  total: number;
  page: number;
  pageSize: number;
  isLoading: boolean;
  isError?: boolean;
  onPageChange: (page: number) => void;
  onRetry?: () => void;
}

export function DataRunsTable({
  runs,
  total,
  page,
  pageSize,
  isLoading,
  isError,
  onPageChange,
  onRetry,
}: DataRunsTableProps) {
  if (isLoading) {
    return <SkeletonLoader variant="list" />;
  }

  if (isError) {
    return (
      <Card className="p-6 flex flex-col items-center gap-3 text-center">
        <p className="text-sm text-secondary">Failed to load data runs.</p>
        {onRetry && (
          <Button intent="outline" size="sm" onClick={onRetry}>
            Retry
          </Button>
        )}
      </Card>
    );
  }

  const lastPage = Math.ceil(total / pageSize);
  const rangeStart = (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, total);

  return (
    <Card className="overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border-subtle bg-bg-sunken">
            <th className="px-4 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
              Run Date
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
              Insights
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {runs.map((run) => (
            <tr key={run.id} className="hover:bg-bg-hover transition-colors">
              <td className="px-4 py-3 text-secondary whitespace-nowrap">
                {new Date(run.runDate).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </td>
              <td className="px-4 py-3">
                <Badge intent={statusIntent[run.status]}>{run.status}</Badge>
              </td>
              <td className="px-4 py-3 text-secondary">{run.insights}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
        <span className="text-xs text-secondary">
          Showing {rangeStart}–{rangeEnd} of {total}
        </span>
        <div className="flex gap-2">
          <Button
            intent="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
          >
            Prev
          </Button>
          <Button
            intent="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= lastPage}
          >
            Next
          </Button>
        </div>
      </div>
    </Card>
  );
}
