import { Badge } from '@/components/ui/Badge';
import { useAlertsContext } from '@/store/AlertsContext';
import { useEffect, useState } from 'react';
import { AlertFilters, type AlertFiltersProps } from './components/AlertFilters';
import { AlertList } from './components/AlertList';
import { useAlerts, useDismissAlert, useMarkAlertRead, useMarkAllRead } from './hooks/useAlerts';

export default function Alerts() {
  const [severity, setSeverity] = useState<AlertFiltersProps['severity']>('all');
  const [sort, setSort] = useState<AlertFiltersProps['sort']>('newest');

  const { data: alerts = [], isLoading, isError, refetch } = useAlerts({ severity, sort });
  const { setUnreadCount } = useAlertsContext();

  const markRead = useMarkAlertRead();
  const dismiss = useDismissAlert();
  const markAllRead = useMarkAllRead();

  // Sync unread count to context whenever data loads
  useEffect(() => {
    if (alerts.length > 0 || !isLoading) {
      setUnreadCount(alerts.filter((a) => !a.isRead).length);
    }
  }, [alerts, isLoading, setUnreadCount]);

  const { unreadCount } = useAlertsContext();

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold text-primary">Alerts</h1>
          {unreadCount > 0 && (
            <Badge intent="critical">{unreadCount} unread</Badge>
          )}
        </div>
        {alerts.length > 0 && (
          <button
            className="text-sm text-secondary hover:text-primary transition-colors"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
          >
            Mark all as read
          </button>
        )}
      </div>

      {/* Mutation error */}
      {(markRead.isError || dismiss.isError || markAllRead.isError) && (
        <div className="rounded-md bg-danger-subtle border border-danger-muted px-4 py-3 text-sm text-danger-bright">
          Action failed. Please try again.
        </div>
      )}

      {/* Filters */}
      <AlertFilters
        severity={severity}
        sort={sort}
        onSeverityChange={setSeverity}
        onSortChange={setSort}
      />

      {/* Alert list */}
      <AlertList
        alerts={alerts}
        isLoading={isLoading}
        isError={isError}
        onMarkRead={(id) => markRead.mutate(id)}
        onDismiss={(id) => dismiss.mutate(id)}
        onRetry={refetch}
      />
    </div>
  );
}
