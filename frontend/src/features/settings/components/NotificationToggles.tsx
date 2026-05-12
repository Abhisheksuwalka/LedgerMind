import { useState } from 'react';
import { Switch } from '@/components/ui/Switch';

export function NotificationToggles() {
  const [toggles, setToggles] = useState({
    anomalies: true,
    weeklyReport: true,
    marketing: false,
  });

  const handleToggle = (key: keyof typeof toggles) => {
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="bg-bg-raised border border-border-subtle rounded-lg p-6">
      <div className="border-b border-border-subtle pb-4 mb-5">
        <h3 className="text-lg font-semibold text-primary">Notifications</h3>
        <p className="text-sm text-secondary">Manage how CashPilot communicates with you.</p>
      </div>

      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-primary">Anomaly Alerts</h4>
            <p className="text-sm text-secondary">Receive real-time alerts when anomalies are detected.</p>
          </div>
          <Switch
            checked={toggles.anomalies}
            onCheckedChange={() => handleToggle('anomalies')}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-primary">Weekly Reports</h4>
            <p className="text-sm text-secondary">Get a summary of your financials every Monday morning.</p>
          </div>
          <Switch
            checked={toggles.weeklyReport}
            onCheckedChange={() => handleToggle('weeklyReport')}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-primary">Marketing Updates</h4>
            <p className="text-sm text-secondary">Receive product updates and promotional offers.</p>
          </div>
          <Switch
            checked={toggles.marketing}
            onCheckedChange={() => handleToggle('marketing')}
          />
        </div>
      </div>
    </div>
  );
}
