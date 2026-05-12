import { useNavigate } from 'react-router-dom';
import { AlertCircle, AlertTriangle, Info, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatRelativeTime } from '@/lib/formatters';
import type { Anomaly } from '@/types/snapshot';

interface AnomalyWidgetProps {
  anomalies: Anomaly[];
}

export function AnomalyWidget({ anomalies }: AnomalyWidgetProps) {
  const navigate = useNavigate();

  const handleAskCashPilot = (title: string) => {
    sessionStorage.setItem('chat_initial_prompt', `Tell me more about: ${title}`);
    navigate('/chat');
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle size={20} className="text-danger-default" />;
      case 'warning':
        return <AlertTriangle size={20} className="text-warning-default" />;
      case 'info':
      default:
        return <Info size={20} className="text-primary-400" />;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-3 pb-2 border-b border-border-subtle mb-0">
        <h3 className="text-lg font-semibold text-primary">Recent Anomalies</h3>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-danger-subtle border border-danger-muted">
          <div className="w-2 h-2 rounded-full bg-danger-default animate-[pulse_1.5s_ease-in-out_infinite]"></div>
          <span className="text-xs font-bold text-danger-bright tracking-wider">LIVE</span>
        </div>
      </CardHeader>
      <CardBody className="p-0">
        {anomalies.length === 0 ? (
          <div className="p-6 text-center text-secondary text-sm">
            No recent anomalies detected.
          </div>
        ) : (
          <div className="flex flex-col">
            {anomalies.map((anomaly, idx) => (
              <div 
                key={anomaly.id} 
                className={`p-4 flex items-start gap-4 ${
                  idx !== anomalies.length - 1 ? 'border-b border-border-subtle' : ''
                }`}
              >
                <div className="mt-0.5">
                  {getSeverityIcon(anomaly.severity)}
                </div>
                <div className="flex-1 flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-medium text-primary">{anomaly.title}</h4>
                    <span className="text-xs text-tertiary">{formatRelativeTime(anomaly.date)}</span>
                    <div className="mt-2">
                      <button 
                        onClick={() => handleAskCashPilot(anomaly.title)}
                        className="text-xs text-primary-400 hover:text-primary-300 font-medium flex items-center gap-1 group"
                      >
                        Ask CashPilot 
                        <ArrowRight size={12} className="transition-transform group-hover:translate-x-0.5" />
                      </button>
                    </div>
                  </div>
                  <Badge intent={anomaly.severity as 'critical' | 'warning' | 'info'}>
                    {anomaly.severity}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
