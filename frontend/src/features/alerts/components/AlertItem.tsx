import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/cn';
import type { Alert } from '@/types/alert';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { useState } from 'react';

interface AlertItemProps {
  alert: Alert;
  onMarkRead: (id: string) => void;
  onDismiss: (id: string) => void;
}

const severityIcon: Record<Alert['severity'], React.ReactNode> = {
  critical: <AlertCircle className="h-5 w-5 text-danger-bright" aria-hidden="true" />,
  warning: <AlertTriangle className="h-5 w-5 text-warning-bright" aria-hidden="true" />,
  info: <Info className="h-5 w-5 text-primary-300" aria-hidden="true" />,
};

const severityIntent: Record<Alert['severity'], 'critical' | 'warning' | 'info'> = {
  critical: 'critical',
  warning: 'warning',
  info: 'info',
};

export function AlertItem({ alert, onMarkRead, onDismiss }: AlertItemProps) {
  const [dismissing, setDismissing] = useState(false);

  function handleDismiss() {
    setDismissing(true);
    // Wait for CSS exit animation to complete before calling onDismiss
    setTimeout(() => onDismiss(alert.id), 300);
  }

  return (
    <div
      data-testid="alert-item"
      data-read={alert.isRead}
      className={cn(
        'group flex items-start gap-3 rounded-lg p-4 transition-all duration-300',
        !alert.isRead
          ? 'border-l-4 border-l-primary-500 bg-bg-raised shadow-sm'
          : 'border-l-4 border-l-transparent bg-transparent',
        dismissing && 'animate-out fade-out-0 slide-out-to-right-4'
      )}
    >
      {/* Severity icon */}
      <div className="mt-0.5 shrink-0">{severityIcon[alert.severity]}</div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-primary">{alert.title}</span>
          <Badge intent={severityIntent[alert.severity]}>{alert.severity}</Badge>
        </div>
        <p className="text-sm text-secondary">{alert.description}</p>
      </div>

      {/* Actions */}
      <div className="flex shrink-0 gap-2 opacity-0 transition-opacity group-hover:opacity-100">
        {!alert.isRead && (
          <Button
            intent="ghost"
            size="sm"
            onClick={() => onMarkRead(alert.id)}
            aria-label="Mark as Read"
          >
            Mark as Read
          </Button>
        )}
        <Button
          intent="ghost"
          size="sm"
          onClick={handleDismiss}
          aria-label="Dismiss"
        >
          Dismiss
        </Button>
      </div>
    </div>
  );
}
