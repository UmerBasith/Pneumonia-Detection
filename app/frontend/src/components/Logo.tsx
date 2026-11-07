export function LogoMark({ className = 'size-8' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden focusable="false">
      <rect width="32" height="32" rx="9" fill="var(--film)" />
      <rect x="0.5" y="0.5" width="31" height="31" rx="8.5" fill="none" stroke="var(--film-line)" />
      <path
        d="M14.6 9.2c-3.9 1-6.6 5.8-6.6 11.4 0 2.6 1 3.9 2.9 3.9 2.7 0 3.7-2.6 3.7-6.6V9.2Z"
        fill="#8fb4f0"
        opacity="0.92"
      />
      <path
        d="M17.4 9.2c3.9 1 6.6 5.8 6.6 11.4 0 2.6-1 3.9-2.9 3.9-2.7 0-3.7-2.6-3.7-6.6V9.2Z"
        fill="#8fb4f0"
        opacity="0.92"
      />
      <path d="M16 5.5v8.2" stroke="#e8eef6" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="20.6" cy="18.6" r="2.3" fill="#ffb35c" />
    </svg>
  )
}

export function Wordmark() {
  return (
    <span className="flex items-center gap-2.5">
      <LogoMark />
      <span className="flex items-baseline gap-1.5">
        <span className="font-display text-[1.15rem] font-[680] tracking-[-0.03em] text-ink">PneumoScan</span>
        <span className="rounded-[5px] border border-line-strong px-1 py-px font-mono text-[0.62rem] font-medium tracking-[0.12em] text-ink-2">
          AI
        </span>
      </span>
    </span>
  )
}
