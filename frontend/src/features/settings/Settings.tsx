import { ProfileForm } from './components/ProfileForm';
import { BusinessProfileForm } from './components/BusinessProfileForm';
import { IntegrationCard } from './components/IntegrationCard';
import { NotificationToggles } from './components/NotificationToggles';
import { useState, useEffect } from 'react';
import { apiFetch, resetData } from '@/lib/api';
import { CheckCircle, XCircle, Loader2, AlertTriangle, Trash2 } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

interface ProviderStatus {
  tax_rate_pct: number;
  providers: { groq: boolean; gemini: boolean; anthropic: boolean };
  active_groq_model: string;
  active_anthropic_model: string;
}

const PROVIDER_META = [
  { key: 'groq',      label: 'Groq',      modelKey: 'active_groq_model',      free: true },
  { key: 'gemini',    label: 'Gemini',    modelKey: null,                      free: true },
  { key: 'anthropic', label: 'Anthropic', modelKey: 'active_anthropic_model',  free: false },
];

export default function Settings() {
  const [stripeConnected, setStripeConnected] = useState(false);
  const [plaidConnected, setPlaidConnected] = useState(false);
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [providerLoading, setProviderLoading] = useState(true);
  const [isConfirmingReset, setIsConfirmingReset] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    apiFetch<ProviderStatus>('/settings')
      .then(setProviderStatus)
      .catch(() => {/* backend offline — silent */})
      .finally(() => setProviderLoading(false));
  }, []);

  return (
    <main className="p-4 md:p-8 space-y-8 max-w-[1000px] mx-auto w-full pb-20">
      <header>
        <h1 className="text-2xl font-bold text-primary">Settings</h1>
        <p className="text-sm text-secondary mt-1">Manage your account settings and preferences.</p>
      </header>

      <div className="flex flex-col gap-6">
        <ProfileForm />
        <BusinessProfileForm />

        {/* LLM Provider Status */}
        <section className="bg-bg-raised border border-border-subtle rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-primary">LLM Providers</h2>
          {providerLoading && (
            <div className="flex items-center gap-2 text-secondary text-sm">
              <Loader2 size={14} className="animate-spin" /> Checking provider status…
            </div>
          )}
          {providerStatus && (
            <div className="space-y-3">
              {PROVIDER_META.map(({ key, label, modelKey, free }) => {
                const configured = providerStatus.providers[key as keyof typeof providerStatus.providers];
                const model = modelKey ? (providerStatus as any)[modelKey] as string : null;
                return (
                  <div key={key} className="flex items-center justify-between py-2 border-b border-border-subtle last:border-0">
                    <div className="flex items-center gap-2">
                      {configured
                        ? <CheckCircle size={14} className="text-emerald-400" />
                        : <XCircle size={14} className="text-red-400" />}
                      <span className="text-sm font-medium text-primary">{label}</span>
                      {free && <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-900/40 text-emerald-400 font-mono">FREE</span>}
                    </div>
                    <div className="text-right">
                      <span className={`text-xs font-semibold ${configured ? 'text-emerald-400' : 'text-red-400'}`}>
                        {configured ? 'Configured' : 'Not set'}
                      </span>
                      {configured && model && (
                        <p className="text-xs text-tertiary font-mono mt-0.5">{model}</p>
                      )}
                    </div>
                  </div>
                );
              })}
              <p className="text-xs text-tertiary pt-1">Tax rate: {providerStatus.tax_rate_pct}% · Add API keys to <code className="text-primary-400">.env</code> and restart the backend.</p>
            </div>
          )}
        </section>

        <div className="space-y-6">
          <h2 className="text-xl font-bold text-primary mt-4">Integrations</h2>
          <IntegrationCard
            title="Stripe"
            description="Connect to import your revenue data and transactions."
            isConnected={stripeConnected}
            onConnect={() => setStripeConnected(true)}
            onDisconnect={() => setStripeConnected(false)}
          />
          <IntegrationCard
            title="Plaid"
            description="Connect your bank accounts to track expenses and balances."
            isConnected={plaidConnected}
            onConnect={() => setPlaidConnected(true)}
            onDisconnect={() => setPlaidConnected(false)}
          />
        </div>

        <NotificationToggles />

        {/* Danger Zone */}
        <section className="bg-bg-raised border border-red-900/30 rounded-xl p-6 mt-8">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-red-900/20 rounded-lg text-red-500 mt-1">
              <AlertTriangle size={24} />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-red-500">Danger Zone</h2>
              <p className="text-sm text-tertiary mt-1 mb-4">
                Permanently delete all uploaded financial data, pipeline runs, reports, anomalies, and chat history. 
                This action cannot be undone. Your business profile will be reset to a clean state.
              </p>
              
              {isConfirmingReset ? (
                <div className="flex items-center gap-3 bg-bg-sunken p-4 rounded-lg border border-red-900/50">
                  <p className="text-sm font-medium text-primary">Are you absolutely sure?</p>
                  <div className="ml-auto flex gap-2">
                    <button 
                      className="px-3 py-1.5 text-xs font-medium bg-bg-hover hover:bg-bg-raised border border-border-default rounded-md transition-colors"
                      onClick={() => setIsConfirmingReset(false)}
                      disabled={isResetting}
                    >
                      Cancel
                    </button>
                    <button 
                      className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-red-600 hover:bg-red-500 text-white rounded-md transition-colors"
                      onClick={async () => {
                        setIsResetting(true);
                        try {
                          await resetData();
                          await queryClient.invalidateQueries(); // Invalidate everything
                          setIsConfirmingReset(false);
                          // Optionally show a toast here if a toast system exists
                        } catch (err) {
                          console.error("Failed to reset data", err);
                        } finally {
                          setIsResetting(false);
                        }
                      }}
                      disabled={isResetting}
                    >
                      {isResetting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                      Yes, Delete Everything
                    </button>
                  </div>
                </div>
              ) : (
                <button 
                  className="px-4 py-2 text-sm font-medium border border-red-900/50 text-red-500 hover:bg-red-900/20 hover:text-red-400 rounded-lg transition-colors flex items-center gap-2"
                  onClick={() => setIsConfirmingReset(true)}
                >
                  Clear All Financial Data
                </button>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
