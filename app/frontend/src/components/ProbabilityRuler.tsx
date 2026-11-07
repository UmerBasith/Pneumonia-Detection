import { motion, useReducedMotion } from 'motion/react'

/**
 * Probability of pneumonia on a 0-100 ruler with the decision threshold marked.
 * The threshold tick shows where the model switches from "Normal" to "Pneumonia".
 */
export function ProbabilityRuler({ prob, threshold }: { prob: number; threshold: number }) {
  const reduce = useReducedMotion()
  const p = Math.min(1, Math.max(0, prob))
  const t = Math.min(1, Math.max(0, threshold))
  const pneu = p >= t
  const ticks = Array.from({ length: 11 }, (_, i) => i / 10)
  const tText = `${(t * 100).toFixed(t < 0.1 ? 1 : 0)}%`
  const thrLeft = t > 0.82 ? 'right' : t < 0.18 ? 'left' : 'center'

  return (
    <div>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Pneumonia probability</p>
          <p className="mt-1 font-display text-[3.4rem] leading-none font-[640] tracking-[-0.04em] tabular sm:text-[4rem]">
            {(p * 100).toFixed(1)}
            <span className="ml-0.5 text-[0.5em] font-[560] text-ink-3">%</span>
          </p>
        </div>
      </div>

      <div
        className="relative mt-7 mb-2"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(p * 1000) / 10}
        aria-label={`Pneumonia probability ${(p * 100).toFixed(1)} percent; decision threshold ${tText}`}
      >
        {/* threshold label */}
        <div
          className="absolute -top-6 font-mono text-[0.68rem] tracking-[0.06em] whitespace-nowrap text-ink-3 uppercase"
          style={{
            left: `${t * 100}%`,
            transform: thrLeft === 'center' ? 'translateX(-50%)' : thrLeft === 'right' ? 'translateX(-100%)' : 'none',
          }}
        >
          Threshold {tText}
        </div>
        {/* track */}
        <div className="relative h-3 overflow-hidden rounded-full bg-sunken ring-1 ring-line ring-inset">
          <div className="absolute inset-y-0 right-0 bg-flag/10" style={{ left: `${t * 100}%` }} aria-hidden />
          <motion.div
            className={`absolute inset-y-0 left-0 rounded-full ${pneu ? 'bg-flag' : 'bg-clear'}`}
            initial={reduce ? false : { width: '0%' }}
            animate={{ width: `${p * 100}%` }}
            transition={{ duration: 0.9, ease: [0.2, 0.8, 0.2, 1], delay: 0.1 }}
          />
        </div>
        {/* threshold tick */}
        <div className="absolute -top-1.5 -bottom-1.5 w-[2px] rounded bg-ink" style={{ left: `calc(${t * 100}% - 1px)` }} aria-hidden />
        {/* marker */}
        <motion.div
          className="absolute top-1/2 size-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-surface shadow-2"
          style={{ background: pneu ? 'var(--flag)' : 'var(--clear)' }}
          initial={reduce ? false : { left: '0%' }}
          animate={{ left: `${p * 100}%` }}
          transition={{ duration: 0.9, ease: [0.2, 0.8, 0.2, 1], delay: 0.1 }}
          aria-hidden
        />
      </div>

      {/* scale */}
      <div className="relative mt-3 h-5" aria-hidden>
        {ticks.map((v) => (
          <span key={v} className="absolute top-0 flex -translate-x-1/2 flex-col items-center" style={{ left: `${v * 100}%` }}>
            <span className={`w-px bg-line-strong ${v === 0 || v === 0.5 || v === 1 ? 'h-2' : 'h-1'}`} />
            {(v === 0 || v === 0.5 || v === 1) && (
              <span className="mt-0.5 font-mono text-[0.65rem] text-ink-3">{v * 100}</span>
            )}
          </span>
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[0.78rem] text-ink-3">
        <span>Normal side</span>
        <span>Pneumonia side</span>
      </div>
    </div>
  )
}
