import { useEffect, useMemo } from 'react'
import { ImageOff, RefreshCw } from 'lucide-react'
import { api, type SampleItem } from '../lib/api'
import { samplesCache, scanSession } from '../lib/scanSession'
import { useStore } from '../lib/store'

function loadSamples(force = false) {
  const s = samplesCache.get()
  if (!force && (s.status === 'loading' || s.status === 'ready')) return
  samplesCache.set({ status: 'loading', items: s.items })
  api
    .samples()
    .then((r) => samplesCache.set({ status: 'ready', items: r.items }))
    .catch(() => samplesCache.set({ status: 'error', items: [] }))
}

/** Interleave classes so the tile position never gives the answer away. */
function interleave(items: SampleItem[]): SampleItem[] {
  const pn = items.filter((i) => i.category === 'pneumonia')
  const no = items.filter((i) => i.category === 'normal')
  const out: SampleItem[] = []
  const n = Math.max(pn.length, no.length)
  for (let i = 0; i < n; i++) {
    const pair = i % 2 === 0 ? [no[i], pn[i]] : [pn[i], no[i]]
    for (const p of pair) if (p) out.push(p)
  }
  return out
}

function Tile({
  item,
  label,
  revealed,
  disabled,
  onPick,
}: {
  item: SampleItem
  label: string
  revealed?: string
  disabled: boolean
  onPick: (s: SampleItem) => void
}) {
  const truth =
    revealed === 'PNEUMONIA' ? 'Pneumonia' : revealed === 'NORMAL' ? 'Normal' : revealed === 'not_xray' ? 'Not an X-ray' : null
  return (
    <li>
      <button
        type="button"
        onClick={() => onPick(item)}
        disabled={disabled}
        className="group block w-full text-left disabled:cursor-not-allowed disabled:opacity-60"
        aria-label={`Analyse ${label}${truth ? `, ground truth ${truth}` : ''}`}
      >
        <span className="relative block aspect-square overflow-hidden rounded-xl bg-film ring-1 ring-film-line transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:shadow-2 group-focus-visible:ring-2 group-focus-visible:ring-accent">
          <img
            src={item.thumb_url}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover opacity-90 transition-opacity group-hover:opacity-100"
          />
          {truth && (
            <span
              className={`absolute top-1.5 left-1.5 rounded-md px-1.5 py-0.5 font-mono text-[0.6rem] font-medium tracking-[0.06em] uppercase ${
                revealed === 'PNEUMONIA'
                  ? 'bg-flag text-white'
                  : revealed === 'NORMAL'
                    ? 'bg-clear text-white'
                    : 'bg-ink-2 text-white'
              }`}
            >
              {truth}
            </span>
          )}
        </span>
        <span className="mt-1.5 block font-mono text-[0.7rem] tracking-[0.04em] text-ink-3 group-hover:text-ink">{label}</span>
      </button>
    </li>
  )
}

export function SampleGallery({ onPick, disabled }: { onPick: (s: SampleItem) => void; disabled: boolean }) {
  const { status, items } = useStore(samplesCache)
  const { revealed } = useStore(scanSession)
  useEffect(() => loadSamples(), [])

  const xrays = useMemo(() => interleave(items.filter((i) => i.category !== 'not_xray')), [items])
  const others = useMemo(() => items.filter((i) => i.category === 'not_xray'), [items])

  return (
    <section aria-labelledby="samples-heading" className="mt-14">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="samples-heading" className="text-[1.35rem] font-[650]">
            Try a sample X-ray
          </h2>
          <p className="mt-1 max-w-2xl text-[0.95rem] text-ink-2">
            Real chest X-rays from the held-out test set, never seen during training. The true diagnosis is shown only
            after the model has answered.
          </p>
        </div>
      </div>

      {status === 'loading' || status === 'idle' ? (
        <ul className="mt-5 grid grid-cols-3 gap-3 sm:grid-cols-6 lg:grid-cols-12" aria-label="Loading samples">
          {Array.from({ length: 12 }, (_, i) => (
            <li key={i} className="skeleton aspect-square" />
          ))}
        </ul>
      ) : status === 'error' ? (
        <div className="mt-5 flex flex-wrap items-center gap-3 rounded-2xl border border-dashed border-line-strong p-5 text-ink-2">
          <ImageOff className="size-5 text-ink-3" aria-hidden />
          <p className="text-[0.95rem]">The sample X-rays could not be loaded.</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => loadSamples(true)}>
            <RefreshCw className="size-3.5" aria-hidden /> Retry
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="mt-5 rounded-2xl border border-dashed border-line-strong p-5 text-[0.95rem] text-ink-2">
          No sample X-rays yet. They appear here once the <span className="font-mono text-[0.85em]">sample_xrays</span> folder
          is filled.
        </div>
      ) : (
        <>
          <ul className="mt-5 grid grid-cols-3 gap-3 sm:grid-cols-6 lg:grid-cols-12">
            {xrays.map((it, i) => (
              <Tile
                key={it.id}
                item={it}
                label={`X-ray ${String(i + 1).padStart(2, '0')}`}
                revealed={revealed[it.id]}
                disabled={disabled}
                onPick={onPick}
              />
            ))}
          </ul>
          {others.length > 0 && (
            <div className="mt-6">
              <h3 className="text-[0.95rem] font-[620]">Not X-rays</h3>
              <p className="mt-0.5 text-sm text-ink-3">Try one of these to see the image check turn it away.</p>
              <ul className="mt-3 grid grid-cols-3 gap-3 sm:grid-cols-6 lg:grid-cols-12">
                {others.map((it, i) => (
                  <Tile
                    key={it.id}
                    item={it}
                    label={`Other image ${i + 1}`}
                    revealed={revealed[it.id]}
                    disabled={disabled}
                    onPick={onPick}
                  />
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  )
}
