import { useState } from 'react';
import { Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';


interface IntegrationCardProps {
  title: string;
  description: string;
  isConnected: boolean;
  onConnect: (apiKey: string) => void;
  onDisconnect: () => void;
}

export function IntegrationCard({
  title,
  description,
  isConnected,
  onConnect,
  onDisconnect,
}: IntegrationCardProps) {
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKey) {
      onConnect(apiKey);
    }
  };

  return (
    <div className="bg-bg-raised border border-border-subtle rounded-lg p-6">
      <div className="border-b border-border-subtle pb-4 mb-5 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-primary">{title}</h3>
          <p className="text-sm text-secondary">{description}</p>
        </div>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <>
              <CheckCircle className="w-4 h-4 text-success-default" />
              <span className="text-sm font-medium text-success-default">Connected</span>
            </>
          ) : (
            <>
              <XCircle className="w-4 h-4 text-danger-default" />
              <span className="text-sm font-medium text-danger-default">Disconnected</span>
            </>
          )}
        </div>
      </div>

      {!isConnected ? (
        <form onSubmit={handleSubmit} className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-secondary mb-2" htmlFor={`${title}-apiKey`}>
              API Key
            </label>
            <div className="relative">
              <Input
                id={`${title}-apiKey`}
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API Key"
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="focus:outline-none hover:text-primary transition-colors"
                  >
                    {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                }
              />
            </div>
          </div>
          <Button intent="primary" type="submit" disabled={!apiKey}>
            Connect
          </Button>
        </form>
      ) : (
        <div className="flex justify-between items-center bg-bg-base p-4 rounded-md border border-border-default">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-success-subtle flex items-center justify-center border border-success-muted">
              <CheckCircle className="w-4 h-4 text-success-bright" />
            </div>
            <div>
              <p className="text-sm font-medium text-primary">Integration Active</p>
              <p className="text-xs text-tertiary">Data is syncing automatically.</p>
            </div>
          </div>
          <Button intent="danger" size="sm" onClick={onDisconnect}>
            Disconnect
          </Button>
        </div>
      )}
    </div>
  );
}
