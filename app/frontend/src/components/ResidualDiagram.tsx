/** A residual block: two weight layers F(x) plus the identity shortcut x. */
export function ResidualDiagram() {
  const box = 'fill-[var(--surface)] stroke-[var(--line-strong)]'
  const text = 'fill-[var(--ink)]'
  const sub = 'fill-[var(--ink-3)]'
  return (
    <svg
      viewBox="0 0 720 250"
      className="h-auto w-full"
      role="img"
      aria-labelledby="res-title res-desc"
    >
      <title id="res-title">Residual block</title>
      <desc id="res-desc">
        The input x passes through two convolution layers to give F of x. A shortcut carries x around them unchanged. The
        two are added, so the block outputs F of x plus x, then a ReLU.
      </desc>
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0 0 10 5 0 10z" className="fill-[var(--ink-3)]" />
        </marker>
        <marker id="arr-accent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0 0 10 5 0 10z" className="fill-[var(--accent)]" />
        </marker>
      </defs>

      {/* skip connection */}
      <path
        d="M70 150 C 70 40, 120 40, 200 40 L 520 40 C 600 40, 600 40, 600 128"
        fill="none"
        className="stroke-[var(--accent)]"
        strokeWidth="2.5"
        strokeDasharray="7 6"
        markerEnd="url(#arr-accent)"
      />
      <rect x="282" y="24" width="156" height="32" rx="16" className="fill-[var(--accent-soft)]" />
      <text x="360" y="45" textAnchor="middle" className="fill-[var(--accent)] font-mono text-[13px] font-medium">
        identity shortcut: x
      </text>

      {/* input */}
      <circle cx="70" cy="170" r="22" className={box} strokeWidth="1.5" />
      <text x="70" y="176" textAnchor="middle" className={`${text} font-mono text-[17px] font-medium`}>
        x
      </text>
      <line x1="92" y1="170" x2="140" y2="170" className="stroke-[var(--ink-3)]" strokeWidth="1.8" markerEnd="url(#arr)" />

      {/* layer 1 */}
      <rect x="144" y="138" width="150" height="64" rx="12" className={box} strokeWidth="1.5" />
      <text x="219" y="166" textAnchor="middle" className={`${text} text-[15px] font-semibold`}>
        3×3 conv
      </text>
      <text x="219" y="187" textAnchor="middle" className={`${sub} font-mono text-[12px]`}>
        BatchNorm · ReLU
      </text>
      <line x1="294" y1="170" x2="340" y2="170" className="stroke-[var(--ink-3)]" strokeWidth="1.8" markerEnd="url(#arr)" />

      {/* layer 2 */}
      <rect x="344" y="138" width="150" height="64" rx="12" className={box} strokeWidth="1.5" />
      <text x="419" y="166" textAnchor="middle" className={`${text} text-[15px] font-semibold`}>
        3×3 conv
      </text>
      <text x="419" y="187" textAnchor="middle" className={`${sub} font-mono text-[12px]`}>
        BatchNorm
      </text>
      <line x1="494" y1="170" x2="574" y2="170" className="stroke-[var(--ink-3)]" strokeWidth="1.8" markerEnd="url(#arr)" />
      <text x="534" y="160" textAnchor="middle" className={`${sub} font-mono text-[12px]`}>
        F(x)
      </text>

      {/* add */}
      <circle cx="600" cy="170" r="24" className="fill-[var(--accent)]" />
      <text x="600" y="178" textAnchor="middle" className="fill-[var(--accent-ink)] text-[24px] font-semibold">
        +
      </text>
      <line x1="624" y1="170" x2="652" y2="170" className="stroke-[var(--ink-3)]" strokeWidth="1.8" markerEnd="url(#arr)" />
      <text x="688" y="175" textAnchor="middle" className={`${text} font-mono text-[13px] font-medium`}>
        ReLU
      </text>

      {/* brace label */}
      <path d="M150 218 Q 150 230 162 230 L 476 230 Q 488 230 488 218" fill="none" className="stroke-[var(--line-strong)]" strokeWidth="1.5" />
      <text x="319" y="247" textAnchor="middle" className={`${sub} text-[13px]`}>
        the layers only learn the change F(x); output = F(x) + x
      </text>
    </svg>
  )
}
