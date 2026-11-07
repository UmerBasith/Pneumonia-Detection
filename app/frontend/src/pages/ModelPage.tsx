import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { BrainCircuit, Database, ExternalLink, FlaskConical, Layers, RefreshCw, TriangleAlert, X } from 'lucide-react'
import { api, errorMessage, type FigureItem, type ModelInfo } from '../lib/api'
import { normaliseMetrics, type TestMetrics } from '../lib/metrics'
import { pct } from '../lib/format'
import { MODEL_LIMITATION, SOURCES } from '../content/medical'
import { ResidualDiagram } from '../components/ResidualDiagram'
import { PageHeader } from '../components/ui'

const KERMANY = { accuracy: 0.928, sensitivity: 0.932, specificity: 0.901, auc: 0.968 }

function Metric({ label, value, hint, base }: { label: string; value: number | null; hint: string; base?: number }) {
  return (
    <div className="bg-surface p-5 sm:p-6">
      <p className="text-[0.85rem] font-medium text-ink-3">{label}</p>
      <p className="mt-2 font-display text-[2.9rem] leading-none font-[650] tracking-[-0.04em] tabular sm:text-[3.4rem]">
        {value === null ? '–' : (value * 100).toFixed(1)}
        {value !== null && <span className="ml-0.5 text-[0.45em] font-[560] text-ink-3">%</span>}
      </p>
      <p className="mt-3 text-[0.85rem] leading-snug text-ink-2">{hint}</p>
      {base !== undefined && value !== null && (
        <p className="mt-2 font-mono text-[0.7rem] text-ink-3">Kermany et al. 2018: {(base * 100).toFixed(1)}%</p>
      )}
    </div>
  )
}

function Confusion({ t }: { t: TestMetrics }) {
  if (!t.cm) return <p className="text-ink-3">Confusion matrix not available.</p>
  const { tn, fp, fn, tp } = t.cm
  const total = tn + fp + fn + tp
  const cell = (n: number, good: boolean, title: string, sub: string) => (
    <div
      className={`flex flex-col justify-between rounded-xl p-4 ring-1 ${good ? 'bg-accent-soft ring-accent/20' : 'bg-surface-2 ring-line'}`}
      style={{ minHeight: 120 }}
    >
      <span className="text-[0.78rem] font-medium text-ink-3">{title}</span>
      <span>
        <span className="block font-display text-[2.3rem] leading-none font-[650] tracking-[-0.03em] tabular">{n}</span>
        <span className="mt-1 block text-[0.78rem] text-ink-3">
          {sub} · {((n / total) * 100).toFixed(1)}%
        </span>
      </span>
    </div>
  )
  return (
    <div>
      <div className="grid grid-cols-[auto_1fr_1fr] gap-2 text-[0.8rem]">
        <div />
        <p className="text-center font-medium text-ink-2">Model: Normal</p>
        <p className="text-center font-medium text-ink-2">Model: Pneumonia</p>
        <p className="flex items-center pr-2 font-medium text-ink-2 [writing-mode:vertical-rl] rotate-180 justify-center">Truth: Normal</p>
        {cell(tn, true, 'True negative', 'correctly normal')}
        {cell(fp, false, 'False positive', 'false alarm')}
        <p className="flex items-center pr-2 font-medium text-ink-2 [writing-mode:vertical-rl] rotate-180 justify-center">Truth: Pneumonia</p>
        {cell(fn, false, 'False negative', 'missed')}
        {cell(tp, true, 'True positive', 'caught')}
      </div>
      <p className="mt-3 text-[0.82rem] text-ink-3">
        {total} test X-rays. Shaded cells are correct answers.
      </p>
    </div>
  )
}

function FigureCard({ f, onOpen }: { f: FigureItem; onOpen: (f: FigureItem) => void }) {
  return (
    <figure className="card overflow-hidden">
      <button type="button" className="block w-full bg-white p-3" onClick={() => onOpen(f)} aria-label={`Enlarge: ${f.title}`}>
        <img src={f.url} alt={f.title} className="mx-auto h-56 w-full object-contain" />
      </button>
      <figcaption className="border-t border-line px-4 py-3 text-[0.9rem] font-medium">{f.title}</figcaption>
    </figure>
  )
}

export default function ModelPage() {
  const [info, setInfo] = useState<ModelInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [big, setBig] = useState<FigureItem | null>(null)
  const dlg = useRef<HTMLDialogElement>(null)

  const load = useCallback(() => {
    setError(null)
    api
      .modelInfo()
      .then(setInfo)
      .catch((e) => setError(errorMessage(e)))
  }, [])
  useEffect(() => load(), [load])

  useEffect(() => {
    const d = dlg.current
    if (!d) return
    if (big && !d.open) d.showModal()
    if (!big && d.open) d.close()
  }, [big])

  const m = useMemo(() => normaliseMetrics(info?.metrics ?? null), [info])
  const t = m?.test ?? null
  const figures = info?.figures ?? []
  const arch = figures.find((f) => f.name.toLowerCase().startsWith('architecture'))
  const others = figures.filter((f) => f !== arch)
  const card = info?.model_card ?? null
  const cardList = (k: string): string[] =>
    card && Array.isArray(card[k]) ? (card[k] as unknown[]).filter((x): x is string => typeof x === 'string') : []
  const intended = card && typeof card.intended_use === 'string' ? card.intended_use : null
  const notFor = cardList('not_intended_for')
  const limits = cardList('limitations').length
    ? [MODEL_LIMITATION, ...cardList('limitations')]
    : [
        MODEL_LIMITATION,
        'Deep-learning pneumonia models can score lower on X-rays from hospitals they were not trained on (Zech et al., PLOS Medicine 2018).',
        'It answers one question only: normal or pneumonia. It cannot detect other diseases or say which germ is the cause.',
        'The heatmap shows where the model looked. It is not proof of disease and can highlight areas outside the lungs.',
        'The image check that turns away non-X-rays is a safeguard, not a guarantee.',
      ]

  return (
    <div>
      <PageHeader eyebrow="The model · ResNet ensemble with Grad-CAM" title="How well does it read X-rays?">
        Every number on this page comes from the official held-out test set of {t?.n ?? 624} chest X-rays. The model never
        saw them during training, and the decision threshold was chosen on a separate validation split.
      </PageHeader>

      {info?.mode === 'mock' && t && (
        <p className="mb-6 flex items-center gap-2 rounded-xl bg-caution-soft px-4 py-3 text-[0.9rem] text-ink">
          <FlaskConical className="size-4 shrink-0 text-caution" aria-hidden />
          The app is running the mock model right now (demo mode). The test results below belong to the trained model.
        </p>
      )}

      {error ? (
        <div className="card flex flex-col items-center gap-3 p-10 text-center">
          <p className="font-semibold">Could not load the model details</p>
          <p className="text-sm text-ink-2">{error}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={load}>
            <RefreshCw className="size-3.5" aria-hidden /> Retry
          </button>
        </div>
      ) : !info ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4" aria-busy="true">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="skeleton h-48" />
          ))}
        </div>
      ) : !t ? (
        <div className="card p-8 text-center">
          <p className="font-semibold">Test results are not available yet</p>
          <p className="mt-1 text-ink-2">They appear here once the model has been trained and evaluated (models/metrics.json).</p>
        </div>
      ) : (
        <>
          <section aria-label="Headline test metrics" className="grid grid-cols-1 gap-px overflow-hidden rounded-[18px] border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Accuracy" value={t.accuracy} hint="Share of all test X-rays it labelled correctly." base={KERMANY.accuracy} />
            <Metric label="Sensitivity (recall)" value={t.sensitivity} hint="Of the X-rays with pneumonia, how many it caught." base={KERMANY.sensitivity} />
            <Metric label="Specificity" value={t.specificity} hint="Of the normal X-rays, how many it correctly called normal." base={KERMANY.specificity} />
            <Metric label="ROC-AUC" value={t.auc} hint="How well it ranks sick above healthy across every threshold (100% = perfect)." base={KERMANY.auc} />
          </section>
          <p className="mt-3 text-[0.8rem] text-ink-3">
            Comparison: the dataset authors’ own model (Kermany et al., Cell 2018) on the same test set, as reported in{' '}
            <a className="underline underline-offset-2 hover:text-ink" href="https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/" target="_blank" rel="noreferrer noopener">
              Chumbita et al. 2020
            </a>
            .
          </p>

          <div className="mt-8 grid gap-6 lg:grid-cols-12">
            <section className="card p-6 sm:p-7 lg:col-span-7" aria-labelledby="cm-h">
              <h2 id="cm-h" className="text-[1.2rem] font-[650]">
                Confusion matrix
              </h2>
              <p className="mt-1 mb-5 text-[0.9rem] text-ink-2">Where the model was right and where it slipped, on the test set.</p>
              <Confusion t={t} />
            </section>
            <section className="card p-6 sm:p-7 lg:col-span-5" aria-labelledby="more-h">
              <h2 id="more-h" className="text-[1.2rem] font-[650]">
                More numbers
              </h2>
              <dl className="mt-4 divide-y divide-line text-[0.95rem]">
                {[
                  ['Precision', pct(t.precision), 'When it says pneumonia, how often it is right'],
                  ['F1 score', pct(t.f1), 'Balance of precision and sensitivity'],
                  ['Balanced accuracy', pct(t.balanced), 'Average of sensitivity and specificity'],
                  ['PR-AUC', pct(t.prAuc), 'Area under the precision–recall curve'],
                  ['Decision threshold', t.threshold?.toFixed(3) ?? '–', m?.thresholdRule ?? 'Chosen on validation data'],
                  ['Ensemble', m?.memberNames.length ? `${m.memberNames.length} ResNets` : '–', m?.tta ? 'with horizontal-flip test-time augmentation' : ''],
                ].map(([k, v, h]) => (
                  <div key={k} className="flex items-start justify-between gap-4 py-2.5">
                    <dt>
                      <span className="font-medium">{k}</span>
                      {h && <span className="block text-[0.8rem] text-ink-3">{h}</span>}
                    </dt>
                    <dd className="font-mono font-medium tabular">{v}</dd>
                  </div>
                ))}
              </dl>
            </section>
          </div>
        </>
      )}

      {/* how ResNet works */}
      <section className="mt-14" aria-labelledby="resnet-h">
        <div className="grid gap-8 lg:grid-cols-12">
          <div className="min-w-0 lg:col-span-5">
            <p className="eyebrow flex items-center gap-2">
              <Layers className="size-3.5" aria-hidden /> How ResNet works
            </p>
            <h2 id="resnet-h" className="display mt-3 text-[2.2rem]">
              Learn the change, keep the rest.
            </h2>
            <div className="prose-calm mt-4 text-[0.98rem] text-ink-2">
              <p>
                A convolutional network looks at an X-ray through many stacked layers. Early layers pick up edges and
                textures; deeper layers combine them into shapes such as ribs, the heart border or patchy white areas.
              </p>
              <p>
                Before ResNet, simply stacking more layers often made a network train <em>worse</em>, not better (the
                “degradation” problem). ResNet (He et al., 2015) fixes this with a <strong className="text-ink">skip connection</strong>:
                each block adds its input straight to its output, so it only has to learn the change F(x). If a block has
                nothing useful to add, it can pass x through untouched, and the gradient also flows back along the shortcut.
                That is why networks with 18, 34 or 50 layers train reliably.
              </p>
              <p>
                PneumoScan starts from ResNets pre-trained on ImageNet photos and fine-tunes them on chest X-rays.
                Grad-CAM then follows the gradient of the answer back to the last convolutional layer to show which
                regions mattered most.
              </p>
            </div>
          </div>
          <div className="min-w-0 lg:col-span-7">
            <div className="card p-5 sm:p-7">
              <ResidualDiagram />
            </div>
            {m && m.members.length > 0 && (
              <div className="card relative mt-4 overflow-x-auto">
                <table className="w-full min-w-[520px] text-left text-[0.9rem]">
                  <caption className="px-5 pt-4 text-left text-[0.95rem] font-[640]">Ensemble members (test set, each on its own)</caption>
                  <thead className="text-[0.75rem] text-ink-3">
                    <tr className="border-b border-line">
                      <th scope="col" className="px-5 py-2.5 font-medium">Model</th>
                      <th scope="col" className="px-2 py-2.5 font-medium">Input</th>
                      <th scope="col" className="px-2 py-2.5 font-medium">Accuracy</th>
                      <th scope="col" className="px-2 py-2.5 font-medium">Sensitivity</th>
                      <th scope="col" className="px-2 py-2.5 font-medium">Specificity</th>
                      <th scope="col" className="px-5 py-2.5 font-medium">AUC</th>
                    </tr>
                  </thead>
                  <tbody>
                    {m.members.map((r) => (
                      <tr key={r.name} className="border-b border-line last:border-0">
                        <td className="px-5 py-2.5 font-mono text-[0.85rem]">{r.arch}</td>
                        <td className="px-2 py-2.5 tabular">{r.res ? `${r.res} px` : '–'}</td>
                        <td className="px-2 py-2.5 tabular">{pct(r.accuracy)}</td>
                        <td className="px-2 py-2.5 tabular">{pct(r.sensitivity)}</td>
                        <td className="px-2 py-2.5 tabular">{pct(r.specificity)}</td>
                        <td className="px-5 py-2.5 tabular">{r.auc === null ? '–' : r.auc.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* figures */}
      {(arch || others.length > 0) && (
        <section className="mt-14" aria-labelledby="fig-h">
          <h2 id="fig-h" className="text-[1.5rem] font-[650]">
            Figures from training and testing
          </h2>
          {arch && (
            <figure className="card mt-5 overflow-hidden">
              <button type="button" className="block w-full bg-white p-4" onClick={() => setBig(arch)} aria-label={`Enlarge: ${arch.title}`}>
                <img src={arch.url} alt={arch.title} className="mx-auto max-h-[420px] w-full object-contain" />
              </button>
              <figcaption className="border-t border-line px-4 py-3 text-[0.9rem] font-medium">{arch.title}</figcaption>
            </figure>
          )}
          {others.length > 0 && (
            <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {others.map((f) => (
                <FigureCard key={f.url} f={f} onOpen={setBig} />
              ))}
            </div>
          )}
        </section>
      )}

      {/* data + limits */}
      <div className="mt-14 grid gap-6 lg:grid-cols-2">
        <section className="card p-6 sm:p-7" aria-labelledby="data-h">
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-xl bg-accent-soft text-accent">
              <Database className="size-[1.1rem]" aria-hidden />
            </span>
            <h2 id="data-h" className="text-[1.2rem] font-[650]">
              Dataset and intended use
            </h2>
          </div>
          <p className="mt-4 text-[0.95rem] text-ink-2">
            Chest X-Ray Images (Pneumonia), Kermany et al., <em>Cell</em> 2018. Paediatric patients aged 1–5 from Guangzhou
            Women and Children’s Medical Center. Licence CC BY 4.0.
          </p>
          {m?.dataset?.counts && <CountsTable counts={m.dataset.counts} patients={m.dataset.patients} />}
          {m?.dataset?.split && <p className="mt-4 text-[0.85rem] text-ink-3">Split: {m.dataset.split}.</p>}
          {intended && (
            <div className="mt-5 border-t border-line pt-4">
              <h3 className="font-semibold">Intended use</h3>
              <p className="mt-1 text-[0.92rem] text-ink-2">{intended}</p>
              {notFor.length > 0 && (
                <>
                  <h3 className="mt-3 font-semibold">Not intended for</h3>
                  <ul className="mt-1 space-y-1.5 text-[0.92rem] text-ink-2">
                    {notFor.map((x) => (
                      <li key={x} className="flex gap-2.5">
                        <span className="mt-[0.55rem] size-1.5 shrink-0 rounded-full bg-ink-3" aria-hidden />
                        {x}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}
          <a
            className="mt-3 inline-flex items-center gap-1 text-[0.85rem] font-medium text-accent hover:underline"
            href="https://doi.org/10.17632/rscbjbr9sj.2"
            target="_blank"
            rel="noreferrer noopener"
          >
            Mendeley Data, DOI 10.17632/rscbjbr9sj.2 <ExternalLink className="size-3.5" aria-hidden />
          </a>
        </section>

        <section className="card p-6 sm:p-7" aria-labelledby="lim-h">
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-xl bg-caution-soft text-caution">
              <TriangleAlert className="size-[1.1rem]" aria-hidden />
            </span>
            <h2 id="lim-h" className="text-[1.2rem] font-[650]">
              Limitations
            </h2>
          </div>
          <ul className="mt-4 space-y-2.5 text-[0.95rem] text-ink-2">
            {limits.map((s) => (
              <li key={s} className="flex gap-2.5">
                <span className="mt-[0.6rem] size-1.5 shrink-0 rounded-full bg-ink-3" aria-hidden />
                {s}
              </li>
            ))}
          </ul>
          <p className="mt-4 text-[0.8rem] text-ink-3">
            Source:{' '}
            <a className="underline underline-offset-2 hover:text-ink" href={SOURCES.zech2018.url} target="_blank" rel="noreferrer noopener">
              {SOURCES.zech2018.title}
            </a>
          </p>
        </section>
      </div>

      {m?.version && (
        <p className="mt-6 flex items-center gap-2 font-mono text-[0.75rem] text-ink-3">
          <BrainCircuit className="size-3.5" aria-hidden /> {m.version}
        </p>
      )}

      <dialog
        ref={dlg}
        onClose={() => setBig(null)}
        onClick={(e) => e.target === dlg.current && setBig(null)}
        className="m-auto max-h-[92vh] w-[min(1200px,calc(100vw-24px))] overflow-hidden rounded-2xl border border-line bg-surface p-0 text-ink shadow-3 backdrop:bg-[rgb(6_11_17/0.7)]"
        aria-label={big?.title ?? 'Figure'}
      >
        {big && (
          <div className="flex max-h-[92vh] flex-col">
            <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
              <p className="font-medium">{big.title}</p>
              <button type="button" className="btn btn-ghost btn-icon size-9" onClick={() => setBig(null)} aria-label="Close" autoFocus>
                <X className="size-4" aria-hidden />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-auto bg-white p-4">
              <img src={big.url} alt={big.title} className="mx-auto h-auto max-h-[80vh] w-auto max-w-full object-contain" />
            </div>
          </div>
        )}
      </dialog>
    </div>
  )
}

function CountsTable({ counts, patients }: { counts: Record<string, unknown>; patients: unknown }) {
  const splits = Object.entries(counts).filter(([, v]) => typeof v === 'object' && v !== null) as [string, Record<string, number>][]
  if (!splits.length) return null
  const pat = (typeof patients === 'object' && patients !== null ? patients : {}) as Record<string, number>
  const label: Record<string, string> = { train: 'Training', val: 'Validation', test: 'Test (held out)' }
  return (
    <table className="mt-4 w-full text-left text-[0.9rem]">
      <thead className="text-[0.75rem] text-ink-3">
        <tr className="border-b border-line">
          <th scope="col" className="py-2 font-medium">Split</th>
          <th scope="col" className="py-2 font-medium">Normal</th>
          <th scope="col" className="py-2 font-medium">Pneumonia</th>
          <th scope="col" className="py-2 font-medium">Total</th>
          {Object.keys(pat).length > 0 && <th scope="col" className="py-2 font-medium">Patients</th>}
        </tr>
      </thead>
      <tbody>
        {splits.map(([s, c]) => (
          <tr key={s} className="border-b border-line last:border-0">
            <th scope="row" className="py-2 font-medium">{label[s] ?? s}</th>
            <td className="py-2 tabular">{c.NORMAL ?? '–'}</td>
            <td className="py-2 tabular">{c.PNEUMONIA ?? '–'}</td>
            <td className="py-2 font-medium tabular">{(c.NORMAL ?? 0) + (c.PNEUMONIA ?? 0)}</td>
            {Object.keys(pat).length > 0 && <td className="py-2 tabular">{pat[s] ?? '–'}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
