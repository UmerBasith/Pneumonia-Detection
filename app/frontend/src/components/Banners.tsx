import { FlaskConical, RefreshCw, ServerOff } from 'lucide-react'
import { useStatus } from '../lib/contexts'

/** Global banners: demo (mock model) mode and server offline. */
export function GlobalBanners() {
  const { health, connection, refresh } = useStatus()

  if (connection === 'offline') {
    return (
      <div role="alert" className="border-b border-flag/30 bg-flag-soft">
        <div className="mx-auto flex max-w-[1240px] 2xl:max-w-[1400px] flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5 text-sm sm:px-6">
          <ServerOff className="size-4 shrink-0 text-flag" aria-hidden />
          <p className="font-medium text-ink">
            The PneumoScan server is not responding.
            <span className="font-normal text-ink-2"> Keep the start.bat window open, then retry.</span>
          </p>
          <button type="button" onClick={refresh} className="btn btn-secondary btn-sm ml-auto h-8">
            <RefreshCw className="size-3.5" aria-hidden />
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (health?.mode === 'mock') {
    return (
      <div
        role="status"
        className="border-b border-caution/40 text-ink"
        style={{
          background:
            'repeating-linear-gradient(-45deg, var(--caution-soft) 0 14px, color-mix(in srgb, var(--caution-soft) 70%, var(--caution) 12%) 14px 28px)',
        }}
      >
        <div className="mx-auto flex max-w-[1240px] 2xl:max-w-[1400px] flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5 text-sm sm:px-6">
          <FlaskConical className="size-4 shrink-0 text-caution" aria-hidden />
          <p>
            <strong className="font-mono text-[0.8rem] tracking-[0.08em] uppercase">Demo mode – mock model.</strong>{' '}
            <span className="text-ink-2">
              Results are simulated, not real predictions.
              {health.mock_reason ? ` Reason: ${health.mock_reason}` : ''}
            </span>
          </p>
        </div>
      </div>
    )
  }

  return null
}
