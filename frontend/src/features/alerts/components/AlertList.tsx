import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { SkeletonLoader } from '@/components/ui/SkeletonLoader';
import type { Alert } from '@/types/alert';
import { AlertItem } from './AlertItem';

interface AlertListProps {
  alerts: Alert[];
  isLoading: boolean;
  isError?: boolean;
  onMarkRead: (id: string) => void;
  onDismiss: (id: string) => void;
  onRetry?: () => void;
}

export function AlertList({ alerts, isLoading, isError, onMarkRead, onDismiss, onRetry }: AlertListProps) {
  if (isLoading) {
    return <SkeletonLoader variant="list" />;
  }

  if (isError) {
    return (
      <Card className="p-6 flex flex-col items-center gap-3 text-center">
        <p className="text-sm text-secondary">Failed to load alerts.</p>
        {onRetry && (
          <Button intent="outline" size="sm" onClick={onRetry}>
            Retry
          </Button>
        )}
      </Card>
    );
  }

  if (alerts.length === 0) {
    return (
      <Card className="p-10 flex items-center justify-center">
        <p className="text-sm text-secondary">No alerts to display.</p>
      </Card>
    );
  }

  return (
    <Card className="divide-y divide-border-subtle overflow-hidden">
      {alerts.map((alert) => (
        <AlertItem key={alert.id} alert={alert} onMarkRead={onMarkRead} onDismiss={onDismiss} />
      ))}
    </Card>
  );
}
