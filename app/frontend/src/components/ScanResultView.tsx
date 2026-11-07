import { useEffect, useState, type ReactNode } from 'react'
import { motion } from 'motion/react'
import { CircleAlert, CircleCheck, FileDown, FlaskConical, Info, Save, Target } from 'lucide-react'
import { api, downloadFile, errorMessage, type ScanRecord } from '../lib/api'
import { useToast } from '../lib/contexts'
import { dateTime } from '../lib/format'
import { useTestMetrics } from '../lib/modelInfo'
import { ageError, draftFromScan, sameDraft, type PatientDraft } from '../lib/patient'
import { DISCLAIMER, RESULT_TEXT } from '../content/medical'
import { PatientFields } from './PatientFields'
import { ProbabilityRuler } from './ProbabilityRuler'
import { XrayViewer } from './XrayViewer'
import { RiskBadge, Spinner } from './ui'

function Stat({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-xl bg-surface-2 px-3.5 py-3 ring-1 ring-line">
      <dt className="text-[0.75rem] font-medium text-ink-3">{label}</dt>
      <dd className="mt-1 text-[1.02rem] font-semibold text-ink tabular">{children}</dd>
    </div>
  )
}

const SOURCE_LABEL = { scan: 'Upload', sample: 'Sample X-ray', triage: 'Triage queue' } as const

export function ScanResultView({
  scan: initial,
  actions,
  onUpdated,
}: {
  scan: ScanRecord
  actions?: ReactNode
  onUpdated?: (s: ScanRecord) => void
}) {
  const toast = useToast()
  const metrics = useTestMetrics()
  const [scan, setScan] = useState(initial)
  const [draft, setDraft] = useState<PatientDraft>(() => draftFromScan(initial))
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    setScan(initial)
    setDraft(draftFromScan(initial))
  }, [initial])

  const pneu = scan.label === 'PNEUMONIA'
  const text = RESULT_TEXT[scan.label]
  const dirty = !sameDraft(draft, draftFromScan(scan))
  const invalid = !!ageError(draft.age)

  async function save(quiet = false): Promise<ScanRecord | null> {
    if (invalid) {
      toast.push('error', 'Check the age', ageError(draft.age) ?? undefined)
      return null
    }
    setSaving(true)
    try {
      const updated = await api.updateScan(scan.id, {
        name: draft.name,
        age: draft.age.trim() === '' ? null : Number(draft.age),
        sex: draft.sex,
        patient_id: draft.patient_id,
        symptoms: draft.symptoms,
        doctor_notes: draft.notes,
      })
      setScan(updated)
      setDraft(draftFromScan(updated))
      onUpdated?.(updated)
      if (!quiet) toast.push('success', 'Notes saved', 'They will appear in the PDF report.')
      return updated
    } catch (err) {
      toast.push('error', 'Could not save notes', errorMessage(err))
      return null
    } finally {
      setSaving(false)
    }
  }

  async function download() {
    setDownloading(true)
    try {
      if (dirty) {
        const ok = await save(true)
        if (!ok) return
      }
      await downloadFile(scan.report_url, `PneumoScan_Report_${scan.id}.pdf`)
      toast.push('success', 'Report downloaded', `PneumoScan_Report_${scan.id}.pdf`)
    } catch (err) {
      toast.push('error', 'Could not download the report', errorMessage(err))
    } finally {
      setDownloading(false)
    }
  }

  const gt = scan.ground_truth
  const match = gt ? gt === scan.label : null

  return (
    <div>
      {/* header row */}
      <div className="flex flex-col gap-4 pt-8 pb-6 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <p className="eyebrow">
            Result · {SOURCE_LABEL[scan.source] ?? 'Upload'} · {dateTime(scan.created_at)}
          </p>
          <h1 className="mt-2 flex flex-wrap items-baseline gap-x-3 font-display text-[1.9rem] font-[640] tracking-[-0.03em] sm:text-[2.3rem]">
            <span>Scan</span>
            <span className="font-mono text-[0.62em] font-medium tracking-normal text-ink-2">{scan.id}</span>
          </h1>
          {scan.filename && <p className="mt-1 truncate text-sm text-ink-3">{scan.filename}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn btn-primary" onClick={download} disabled={downloading}>
            {downloading ? <Spinner /> : <FileDown className="size-4" aria-hidden />}
            Download PDF report
          </button>
          {actions}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        {/* viewer + notes */}
        <div className="contents min-w-0 lg:col-span-7 lg:flex lg:flex-col lg:gap-6">
          <div className="order-1 min-w-0 lg:order-none">
            <XrayViewer images={scan.images} scanId={scan.id} createdAt={scan.created_at} modelVersion={scan.model_version} />
          </div>

          <section className="card order-3 p-5 sm:p-6 lg:order-none" aria-labelledby="pt-heading">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 id="pt-heading" className="text-[1.15rem] font-[640]">
                  Patient &amp; notes
                </h2>
                <p className="mt-0.5 text-sm text-ink-3">Saved on this computer and printed on the PDF report.</p>
              </div>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => void save()} disabled={!dirty || saving || invalid}>
                {saving ? <Spinner /> : <Save className="size-4" aria-hidden />}
                {dirty ? 'Save notes' : 'Saved'}
              </button>
            </div>
            <PatientFields value={draft} onChange={setDraft} />
          </section>
        </div>

        {/* result */}
        <motion.section
          className="card relative order-2 h-fit overflow-hidden lg:sticky lg:top-24 lg:order-none lg:col-span-5"
          aria-labelledby="verdict"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
        >
          <div className={`h-1.5 ${pneu ? 'bg-flag' : 'bg-clear'}`} aria-hidden />
          <div className="p-5 sm:p-7">
            {scan.mode === 'mock' && (
              <p className="mb-4 flex items-center gap-2 rounded-lg bg-caution-soft px-3 py-2 text-[0.82rem] font-medium text-caution">
                <FlaskConical className="size-4 shrink-0" aria-hidden />
                Simulated result from the mock model (demo mode)
              </p>
            )}
            <p className="eyebrow">Model output</p>
            <h2 id="verdict" className={`mt-2 flex items-center gap-2.5 text-[1.85rem] font-[660] ${pneu ? 'text-flag' : 'text-clear'}`}>
              {pneu ? <CircleAlert className="size-7 shrink-0" aria-hidden /> : <CircleCheck className="size-7 shrink-0" aria-hidden />}
              {text.headline}
            </h2>
            <div className="mt-3">
              <RiskBadge risk={scan.risk_level} />
            </div>

            <div className="mt-6">
              <ProbabilityRuler prob={scan.prob_pneumonia} threshold={scan.threshold} />
            </div>

            <p className="mt-5 flex gap-2.5 rounded-xl bg-accent-soft px-3.5 py-3 text-[0.86rem] leading-snug text-ink-2">
              <Info className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
              <span>
                The decision threshold is set low on purpose: the model is tuned to rarely miss pneumonia
                {metrics?.test?.sensitivity != null
                  ? ` (sensitivity ${(metrics.test.sensitivity * 100).toFixed(1)}% on the held-out test set)`
                  : ''}
                , so borderline cases are flagged for a doctor to review.
              </span>
            </p>

            <dl className="mt-4 grid grid-cols-2 gap-2.5">
              <Stat label="Decision threshold">{(scan.threshold * 100).toFixed(1)}%</Stat>
              <Stat label="Inference time">{Math.round(scan.inference_ms)} ms</Stat>
            </dl>

            {gt && (
              <div
                className={`mt-3 flex items-center gap-3 rounded-xl px-3.5 py-3 ring-1 ${
                  match ? 'bg-clear-soft ring-clear/25' : 'bg-caution-soft ring-caution/30'
                }`}
              >
                <Target className={`size-5 shrink-0 ${match ? 'text-clear' : 'text-caution'}`} aria-hidden />
                <p className="text-[0.9rem]">
                  <span className="font-semibold">Ground truth: {gt === 'PNEUMONIA' ? 'Pneumonia' : 'Normal'}</span>
                  <span className="text-ink-2">
                    {' '}
                    · {match ? 'the model got this test X-ray right.' : 'the model got this test X-ray wrong.'}
                  </span>
                </p>
              </div>
            )}

            <div className="mt-6 border-t border-line pt-5">
              <h3 className="text-[1rem] font-[640]">What this means</h3>
              <p className="mt-1.5 text-[0.95rem] text-ink-2">{text.explanation}</p>
            </div>

            <div className="mt-5">
              <h3 className="text-[1rem] font-[640]">Recommended next steps</h3>
              <ul className="mt-2 space-y-2">
                {text.steps.map((s) => (
                  <li key={s} className="flex gap-2.5 text-[0.93rem] text-ink-2">
                    <span className="mt-[0.55rem] size-1.5 shrink-0 rounded-full bg-ink-3" aria-hidden />
                    {s}
                  </li>
                ))}
              </ul>
              {RESULT_TEXT.urgent && (
                <p className="mt-3 rounded-xl bg-flag-soft px-3.5 py-3 text-[0.9rem] text-ink">
                  <strong className="text-flag">Get urgent help</strong> {RESULT_TEXT.urgent}
                </p>
              )}
            </div>

            <p className="mt-6 rounded-xl bg-sunken px-3.5 py-3 text-[0.8rem] leading-relaxed text-ink-3">
              <strong className="font-semibold text-ink-2">Not a diagnosis.</strong> {DISCLAIMER}
            </p>
          </div>
        </motion.section>
      </div>
    </div>
  )
}
