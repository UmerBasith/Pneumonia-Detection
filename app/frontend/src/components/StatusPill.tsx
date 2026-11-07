import { useModelState, type Tone } from '../lib/useModelState'

const DOT: Record<Tone, string> = {
  ok: 'bg-clear',
  warn: 'bg-caution',
  demo: 'bg-caution',
  down: 'bg-flag',
}

export function StatusPill({ compact = false }: { compact?: boolean }) {
  const s = useModelState()
  const pulsing = s.tone === 'warn'
  return (
    <span
      className="inline-flex h-8 items-center gap-2 rounded-full border border-line bg-surface px-3 text-[0.8rem] font-medium text-ink-2 shadow-1"
      title={s.detail}
      role="status"
      aria-label={`${s.label}. ${s.detail}`}
    >
      <span className="relative flex size-2">
        {pulsing && <span className={`absolute inline-flex size-full animate-ping rounded-full opacity-60 ${DOT[s.tone]}`} />}
        <span className={`relative inline-flex size-2 rounded-full ${DOT[s.tone]}`} />
      </span>
      <span className={compact ? 'sr-only sm:not-sr-only' : ''}>{s.label}</span>
    </span>
  )
}
