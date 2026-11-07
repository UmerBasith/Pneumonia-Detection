import { useEffect, useId, useRef, type ReactNode } from 'react'
import { AlertTriangle, CircleCheck, CircleAlert, ShieldCheck, TriangleAlert } from 'lucide-react'
import type { Label, RiskLevel } from '../lib/api'

/* ---------------------------------------------------------------- Segmented control */
export function Segmented<T extends string>({
  value,
  onChange,
  options,
  label,
  size = 'md',
  tone = 'surface',
}: {
  value: T
  onChange: (v: T) => void
  options: { value: T; label: ReactNode; title?: string }[]
  label: string
  size?: 'sm' | 'md'
  tone?: 'surface' | 'film'
}) {
  const film = tone === 'film'
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={`inline-flex rounded-xl p-1 ${film ? 'bg-white/[0.06] ring-1 ring-white/10' : 'bg-sunken ring-1 ring-line'}`}
    >
      {options.map((o) => {
        const active = o.value === value
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={active}
            title={o.title}
            onClick={() => onChange(o.value)}
            onKeyDown={(e) => {
              const i = options.findIndex((x) => x.value === value)
              if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault()
                onChange(options[(i + 1) % options.length].value)
              } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault()
                onChange(options[(i - 1 + options.length) % options.length].value)
              }
            }}
            tabIndex={active ? 0 : -1}
            className={`inline-flex items-center gap-1.5 rounded-[9px] font-medium whitespace-nowrap transition-colors ${
              size === 'sm' ? 'h-7 px-2.5 text-[0.8rem]' : 'h-8 px-3 text-[0.85rem]'
            } ${
              active
                ? film
                  ? 'bg-white/[0.14] text-white shadow-sm'
                  : 'bg-surface text-ink shadow-1'
                : film
                  ? 'text-film-ink-2 hover:text-white'
                  : 'text-ink-3 hover:text-ink'
            }`}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

/* ---------------------------------------------------------------- Verdict + risk badges */
export function VerdictBadge({ label, size = 'md' }: { label: Label; size?: 'sm' | 'md' }) {
  const pneu = label === 'PNEUMONIA'
  const Icon = pneu ? CircleAlert : CircleCheck
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold whitespace-nowrap ${
        size === 'sm' ? 'h-6 px-2 text-[0.75rem]' : 'h-7 px-2.5 text-[0.8rem]'
      } ${pneu ? 'bg-flag-soft text-flag' : 'bg-clear-soft text-clear'}`}
    >
      <Icon className={size === 'sm' ? 'size-3.5' : 'size-4'} aria-hidden />
      {pneu ? 'Pneumonia' : 'Normal'}
    </span>
  )
}

const RISK = {
  Low: { Icon: ShieldCheck, cls: 'bg-clear-soft text-clear' },
  Moderate: { Icon: TriangleAlert, cls: 'bg-caution-soft text-caution' },
  High: { Icon: AlertTriangle, cls: 'bg-flag-soft text-flag' },
} as const

export function RiskBadge({ risk, size = 'md' }: { risk: RiskLevel; size?: 'sm' | 'md' }) {
  const r = RISK[risk] ?? RISK.Moderate
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold whitespace-nowrap ${
        size === 'sm' ? 'h-6 px-2 text-[0.75rem]' : 'h-7 px-2.5 text-[0.8rem]'
      } ${r.cls}`}
    >
      <r.Icon className={size === 'sm' ? 'size-3.5' : 'size-4'} aria-hidden />
      {risk} risk
    </span>
  )
}

/* ---------------------------------------------------------------- Dialog (native <dialog>) */
export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel,
  onConfirm,
  onClose,
  danger = true,
  busy = false,
}: {
  open: boolean
  title: string
  body: ReactNode
  confirmLabel: string
  onConfirm: () => void
  onClose: () => void
  danger?: boolean
  busy?: boolean
}) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) d.showModal()
    if (!open && d.open) d.close()
  }, [open])
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(e) => {
        e.preventDefault()
        if (!busy) onClose()
      }}
      onClick={(e) => {
        if (e.target === ref.current && !busy) onClose()
      }}
      className="m-auto w-[min(440px,calc(100vw-32px))] rounded-2xl border border-line bg-surface p-0 text-ink shadow-3 backdrop:bg-[rgb(6_11_17/0.55)] backdrop:backdrop-blur-[2px]"
    >
      <div className="p-6">
        <h2 id={titleId} className="text-xl font-[650]">
          {title}
        </h2>
        <div className="mt-2 text-[0.95rem] text-ink-2">{body}</div>
        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={busy} autoFocus>
            Cancel
          </button>
          <button
            type="button"
            className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`}
            onClick={onConfirm}
            disabled={busy}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  )
}

/* ---------------------------------------------------------------- Page header */
export function PageHeader({
  eyebrow,
  title,
  children,
  actions,
}: {
  eyebrow: string
  title: ReactNode
  children?: ReactNode
  actions?: ReactNode
}) {
  return (
    <div className="flex flex-col gap-5 pt-10 pb-8 md:flex-row md:items-end md:justify-between md:pt-14">
      <div className="max-w-3xl">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="display mt-3 text-[2.4rem] sm:text-[3.1rem]">{title}</h1>
        {children && <div className="mt-4 max-w-2xl text-[1.05rem] text-ink-2">{children}</div>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

export function Spinner({ className = 'size-4' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={`animate-spin ${className}`} aria-hidden>
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeOpacity="0.2" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}
