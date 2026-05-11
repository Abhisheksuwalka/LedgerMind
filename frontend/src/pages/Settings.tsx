import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface SettingsData {
  tax_rate_pct: number
  providers: {
    groq: boolean
    gemini: boolean
    anthropic: boolean
  }
  active_groq_model: string
  active_anthropic_model: string
}

const PROVIDER_META: Record<string, { label: string; model_key: keyof SettingsData | null; free: boolean }> = {
  groq:      { label: 'Groq',      model_key: 'active_groq_model',      free: true },
  gemini:    { label: 'Gemini',    model_key: null,                      free: true },
  anthropic: { label: 'Anthropic', model_key: 'active_anthropic_model',  free: false },
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/v1/settings`)
      .then((r) => r.json())
      .then(setSettings)
      .catch(() => setError(true))
  }, [])

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* LLM Provider Status */}
      <section className="bg-slate-900 border border-slate-700 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">
          LLM Provider Status
        </h2>

        {error && (
          <p className="text-red-400 text-sm">Could not reach API — is the backend running?</p>
        )}

        {!settings && !error && (
          <p className="text-slate-500 text-sm animate-pulse">Loading provider status…</p>
        )}

        {settings && (
          <div className="space-y-3">
            {Object.entries(PROVIDER_META).map(([key, meta]) => {
              const configured = settings.providers[key as keyof typeof settings.providers]
              const modelKey = meta.model_key
              const model = modelKey ? (settings as Record<string, unknown>)[modelKey] as string : null

              return (
                <div key={key} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                        configured ? 'bg-emerald-400' : 'bg-red-500'
                      }`}
                    />
                    <span className="text-slate-200 text-sm font-medium">{meta.label}</span>
                    {meta.free && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-900/60 text-emerald-400 font-mono">
                        FREE
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <span
                      className={`text-xs font-semibold ${
                        configured ? 'text-emerald-400' : 'text-red-400'
                      }`}
                    >
                      {configured ? '● Configured' : '○ Not set'}
                    </span>
                    {configured && model && (
                      <p className="text-slate-500 font-mono text-xs mt-0.5">{model}</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        <p className="text-slate-600 text-xs pt-2 border-t border-slate-800">
          At least one provider must be configured. Add keys to{' '}
          <code className="text-brand-400">.env</code> and restart the backend.
        </p>
      </section>

      {/* Financial Config */}
      {settings && (
        <section className="bg-slate-900 border border-slate-700 rounded-xl p-6 space-y-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">
            Financial Configuration
          </h2>
          <Row label="Tax Rate" value={`${settings.tax_rate_pct}%`} />
        </section>
      )}

      {/* Environment */}
      <section className="bg-slate-900 border border-slate-700 rounded-xl p-6 space-y-3">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">Environment</h2>
        <div className="space-y-2 text-sm">
          <Row label="API URL" value={import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'} />
          <Row label="WebSocket URL" value={import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'} />
          <Row label="Mode" value={import.meta.env.MODE} />
        </div>
      </section>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500 text-sm">{label}</span>
      <span className="text-slate-200 font-mono text-xs">{value}</span>
    </div>
  )
}
