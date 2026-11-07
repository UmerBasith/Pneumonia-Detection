import { useId, useMemo, useState, type ReactNode } from 'react'
import { motion } from 'motion/react'
import { Baby, RotateCcw } from 'lucide-react'
import {
  CRB65_GROUPS,
  CURB65_GROUPS,
  CURB65_PER_SCORE,
  CURB65_SCORE5_NOTE,
  CURB_CRITERIA,
  CURB_NOTE,
  CURB_SOURCES,
  CURB_THRESHOLDS as T,
  type CurbKey,
} from '../content/medical'
import { SourceList } from '../components/Sources'
import { PageHeader, Segmented } from '../components/ui'

type UreaUnit = 'mmol' | 'bun'
type YesNo = 'unset' | 'yes' | 'no'

interface Inputs {
  confusion: YesNo
  urea: string
  ureaUnit: UreaUnit
  noUrea: boolean
  resp: string
  sbp: string
  dbp: string
  age: string
}
const EMPTY: Inputs = { confusion: 'unset', urea: '', ureaUnit: 'mmol', noUrea: false, resp: '', sbp: '', dbp: '', age: '' }

type Parsed = { value: number | null; error: string | null }
function num(s: string, min: number, max: number, unit: string): Parsed {
  const t = s.trim().replace(',', '.')
  if (t === '') return { value: null, error: null }
  const v = Number(t)
  if (!Number.isFinite(v)) return { value: null, error: 'Enter a number.' }
  if (v < min || v > max) return { value: null, error: `Enter a value between ${min} and ${max} ${unit}.` }
  return { value: v, error: null }
}

const RISK_TONE = {
  Low: 'bg-clear-soft text-clear ring-clear/25',
  Intermediate: 'bg-caution-soft text-caution ring-caution/30',
  High: 'bg-flag-soft text-flag ring-flag/25',
} as const

function NumberField({
  label,
  unit,
  value,
  onChange,
  error,
  placeholder,
  hint,
}: {
  label: string
  unit: string
  value: string
  onChange: (v: string) => void
  error: string | null
  placeholder: string
  hint?: string
}) {
  const id = useId()
  return (
    <div className="min-w-0 flex-1">
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          className="field pr-16 font-mono tabular"
          inputMode="decimal"
          value={value}
          placeholder={placeholder}
          maxLength={6}
          aria-invalid={!!error}
          aria-describedby={error || hint ? `${id}-d` : undefined}
          onChange={(e) => onChange(e.target.value)}
        />
        <span className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-[0.8rem] text-ink-3">{unit}</span>
      </div>
      {(error || hint) && (
        <p id={`${id}-d`} className={`mt-1 text-[0.78rem] ${error ? 'text-flag' : 'text-ink-3'}`}>
          {error ?? hint}
        </p>
      )}
    </div>
  )
}

function CriterionRow({
  letter,
  name,
  rule,
  met,
  muted,
  children,
}: {
  letter: string
  name: string
  rule: string
  met: boolean | null
  muted?: boolean
  children: ReactNode
}) {
  return (
    <div className={`grid gap-4 py-5 sm:grid-cols-[3.25rem_1fr] ${muted ? 'opacity-55' : ''}`}>
      <span
        className={`flex size-12 items-center justify-center rounded-xl font-display text-[1.15rem] font-[700] transition-colors ${
          met ? 'bg-accent text-accent-ink' : 'bg-sunken text-ink-3 ring-1 ring-line'
        }`}
        aria-hidden
      >
        {letter}
      </span>
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <h3 className="text-[1.02rem] font-[640]">{name}</h3>
          <span className={`text-[0.8rem] font-medium ${met ? 'text-accent' : 'text-ink-3'}`}>
            {met === null ? 'Not entered' : met ? '+1 point' : '0 points'}
          </span>
        </div>
        <p className="mt-0.5 text-[0.85rem] text-ink-3">{rule}</p>
        <div className="mt-3">{children}</div>
      </div>
    </div>
  )
}

export default function Curb65Page() {
  const [v, setV] = useState<Inputs>(EMPTY)
  const set = <K extends keyof Inputs>(k: K, val: Inputs[K]) => setV((p) => ({ ...p, [k]: val }))

  const r = useMemo(() => {
    const urea = v.ureaUnit === 'mmol' ? num(v.urea, 0, 100, 'mmol/L') : num(v.urea, 0, 300, 'mg/dL')
    const resp = num(v.resp, 0, 80, '/min')
    const sbp = num(v.sbp, 30, 300, 'mmHg')
    const dbp = num(v.dbp, 10, 200, 'mmHg')
    const age = num(v.age, 0, 130, 'years')
    const met: Record<CurbKey, boolean | null> = {
      confusion: v.confusion === 'unset' ? null : v.confusion === 'yes',
      urea: v.noUrea || urea.value === null ? null : v.ureaUnit === 'mmol' ? urea.value > T.ureaMmol : urea.value > T.bunMgDl,
      resp: resp.value === null ? null : resp.value >= T.resp,
      bp:
        sbp.value === null && dbp.value === null
          ? null
          : (sbp.value !== null && sbp.value < T.sbp) || (dbp.value !== null && dbp.value <= T.dbp),
      age: age.value === null ? null : age.value >= T.age,
    }
    const crb = v.noUrea
    const keys = CURB_CRITERIA.map((c) => c.key).filter((k) => !(crb && k === 'urea'))
    const score = keys.reduce((s, k) => s + (met[k] ? 1 : 0), 0)
    const entered = keys.filter((k) => met[k] !== null).length
    const groups = crb ? CRB65_GROUPS : CURB65_GROUPS
    const group = groups.find((g) => g.scores.includes(score)) ?? groups[0]
    return { urea, resp, sbp, dbp, age, met, crb, keys, score, entered, max: keys.length, group }
  }, [v])

  const complete = r.entered === r.max
  const child = r.age.value !== null && r.age.value < 18
  const per = !r.crb ? CURB65_PER_SCORE[r.score] : null
  const name = r.crb ? 'CRB-65' : 'CURB-65'

  return (
    <div>
      <PageHeader eyebrow="For doctors · adults with community-acquired pneumonia" title={<>CURB-65 severity score</>}>
        One point for each sign present. The total estimates 30-day mortality and suggests where care should happen. If blood
        urea is not available, switch to CRB-65.
      </PageHeader>

      <div className="grid items-start gap-6 lg:grid-cols-12">
        <section className="card px-5 sm:px-7 lg:col-span-7" aria-labelledby="crit-h">
          <h2 id="crit-h" className="sr-only">Criteria</h2>
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line py-4">
            <p className="text-sm text-ink-3">
              Mode: <strong className="font-semibold text-ink">{name}</strong> · {r.entered} of {r.max} entered
            </p>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setV(EMPTY)}>
              <RotateCcw className="size-3.5" aria-hidden /> Reset
            </button>
          </div>
          <div className="divide-y divide-line">
            <CriterionRow letter="C" name="Confusion" rule={CURB_CRITERIA[0].rule} met={r.met.confusion}>
              <Segmented<YesNo>
                label="New confusion"
                value={v.confusion}
                onChange={(x) => set('confusion', x)}
                options={[
                  { value: 'unset', label: 'Not assessed' },
                  { value: 'no', label: 'No' },
                  { value: 'yes', label: 'Yes, confused' },
                ]}
              />
            </CriterionRow>

            <CriterionRow letter="U" name="Urea" rule={CURB_CRITERIA[1].rule} met={r.crb ? null : r.met.urea} muted={r.crb}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
                <NumberField
                  label={v.ureaUnit === 'mmol' ? 'Blood urea' : 'Blood urea nitrogen (BUN)'}
                  unit={v.ureaUnit === 'mmol' ? 'mmol/L' : 'mg/dL'}
                  value={v.noUrea ? '' : v.urea}
                  onChange={(x) => set('urea', x)}
                  error={v.noUrea ? null : r.urea.error}
                  placeholder={v.ureaUnit === 'mmol' ? 'e.g. 8.2' : 'e.g. 23'}
                  hint={v.ureaUnit === 'mmol' ? 'Counts if above 7 mmol/L' : 'Counts if above 19 mg/dL'}
                />
                <div className="sm:pt-6">
                  <Segmented<UreaUnit>
                    label="Urea unit"
                    size="sm"
                    value={v.ureaUnit}
                    onChange={(x) => setV((p) => ({ ...p, ureaUnit: x, urea: '' }))}
                    options={[
                      { value: 'mmol', label: 'mmol/L' },
                      { value: 'bun', label: 'BUN mg/dL' },
                    ]}
                  />
                </div>
              </div>
              <label className="mt-3 flex w-fit items-center gap-2.5 text-[0.9rem] text-ink-2">
                <input
                  type="checkbox"
                  className="size-4 accent-[var(--accent)]"
                  checked={v.noUrea}
                  onChange={(e) => set('noUrea', e.target.checked)}
                />
                Urea not available — use CRB-65
              </label>
            </CriterionRow>

            <CriterionRow letter="R" name="Respiratory rate" rule={CURB_CRITERIA[2].rule} met={r.met.resp}>
              <NumberField label="Breaths per minute" unit="/min" value={v.resp} onChange={(x) => set('resp', x)} error={r.resp.error} placeholder="e.g. 24" />
            </CriterionRow>

            <CriterionRow letter="B" name="Blood pressure" rule={CURB_CRITERIA[3].rule} met={r.met.bp}>
              <div className="flex flex-col gap-3 sm:flex-row">
                <NumberField label="Systolic" unit="mmHg" value={v.sbp} onChange={(x) => set('sbp', x)} error={r.sbp.error} placeholder="e.g. 118" />
                <NumberField label="Diastolic" unit="mmHg" value={v.dbp} onChange={(x) => set('dbp', x)} error={r.dbp.error} placeholder="e.g. 72" />
              </div>
            </CriterionRow>

            <CriterionRow letter="65" name="Age" rule={CURB_CRITERIA[4].rule} met={r.met.age}>
              <NumberField label="Age" unit="years" value={v.age} onChange={(x) => set('age', x)} error={r.age.error} placeholder="e.g. 71" />
            </CriterionRow>
          </div>
        </section>

        <aside className="lg:sticky lg:top-24 lg:col-span-5" aria-label={`${name} result`}>
          <div className="card overflow-hidden">
            <div className="p-6 sm:p-7">
              <p className="eyebrow">{name} score</p>
              <div className="mt-2 flex items-end gap-3" aria-live="polite" aria-atomic="true">
                <motion.span
                  key={r.score}
                  initial={{ opacity: 0.4, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="font-display text-[5.5rem] leading-[0.85] font-[650] tracking-[-0.05em] tabular"
                >
                  {r.score}
                </motion.span>
                <span className="pb-2 text-xl font-medium text-ink-3">/ {r.max}</span>
                <span className="sr-only">
                  , {r.group.risk} risk. {r.group.care}.
                </span>
              </div>

              <div className="mt-5 flex gap-1.5" aria-hidden>
                {CURB_CRITERIA.filter((c) => r.keys.includes(c.key)).map((c) => (
                  <span
                    key={c.key}
                    className={`flex h-9 flex-1 items-center justify-center rounded-lg font-display text-[0.95rem] font-[700] transition-colors ${
                      r.met[c.key] ? 'bg-accent text-accent-ink' : r.met[c.key] === null ? 'border border-dashed border-line-strong text-ink-3' : 'bg-sunken text-ink-3'
                    }`}
                  >
                    {c.letter}
                  </span>
                ))}
              </div>

              <div className={`mt-6 rounded-xl px-4 py-3.5 ring-1 ${RISK_TONE[r.group.risk]}`}>
                <p className="text-[0.8rem] font-semibold tracking-[0.04em] uppercase">
                  {r.group.risk} risk · {r.group.group}
                </p>
                <p className="mt-1 text-[1.02rem] font-semibold text-ink">{per?.care ?? r.group.care}</p>
              </div>

              <dl className="mt-4 space-y-3 text-[0.92rem]">
                <div className="flex justify-between gap-4 border-b border-line pb-3">
                  <dt className="text-ink-3">30-day mortality, {r.group.group.toLowerCase()} (Lim et al.)</dt>
                  <dd className="text-right font-semibold tabular">{r.group.mortality}</dd>
                </div>
                {per && (
                  <div className="flex justify-between gap-4 border-b border-line pb-3">
                    <dt className="text-ink-3">At score {r.score}: derivation / validation</dt>
                    <dd className="text-right font-semibold tabular">
                      {per.derivation}
                      <br />
                      {per.validation}
                    </dd>
                  </div>
                )}
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-3">NICE guideline band (secondary)</dt>
                  <dd className="text-right font-medium">{r.group.nice.replace('NICE: ', '')}</dd>
                </div>
              </dl>
              {r.score === 5 && !r.crb && <p className="mt-3 text-[0.78rem] text-ink-3">{CURB65_SCORE5_NOTE}</p>}

              {!complete && (
                <p className="mt-5 rounded-xl bg-sunken px-3.5 py-3 text-[0.85rem] text-ink-2">
                  {r.max - r.entered} criteria not entered yet; they count as 0 until you fill them in.
                </p>
              )}
              {child && (
                <p className="mt-3 flex gap-2.5 rounded-xl bg-caution-soft px-3.5 py-3 text-[0.85rem] text-ink">
                  <Baby className="mt-0.5 size-4 shrink-0 text-caution" aria-hidden />
                  CURB-65 is for adults. For children, use the WHO danger signs on the Learn page.
                </p>
              )}
            </div>
            <div className="border-t border-line bg-surface-2 px-6 py-4 sm:px-7">
              <p className="text-[0.8rem] text-ink-3">{CURB_NOTE}</p>
            </div>
          </div>
        </aside>
      </div>

      <section className="mt-12 grid gap-6 lg:grid-cols-2" aria-labelledby="bands">
        <div className="card p-6">
          <h2 id="bands" className="text-[1.15rem] font-[650]">
            CURB-65 risk groups
          </h2>
          <BandTable groups={CURB65_GROUPS} />
        </div>
        <div className="card p-6">
          <h2 className="text-[1.15rem] font-[650]">CRB-65 (no urea), e.g. in a clinic</h2>
          <BandTable groups={CRB65_GROUPS} />
        </div>
      </section>
      <div className="card mt-6 px-6 pb-5">
        <SourceList ids={CURB_SOURCES} />
      </div>
    </div>
  )
}

function BandTable({ groups }: { groups: typeof CURB65_GROUPS }) {
  return (
    <table className="mt-4 w-full text-left text-[0.88rem]">
      <thead className="text-[0.75rem] text-ink-3">
        <tr className="border-b border-line">
          <th scope="col" className="py-2 pr-3 font-medium">Score</th>
          <th scope="col" className="py-2 pr-3 font-medium">Risk</th>
          <th scope="col" className="py-2 pr-3 font-medium">30-day mortality</th>
          <th scope="col" className="py-2 font-medium">Care</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((g) => (
          <tr key={g.group} className="border-b border-line align-top last:border-0">
            <td className="py-2.5 pr-3 font-mono tabular">
              {g.scores.length > 1 ? `${g.scores[0]}–${g.scores[g.scores.length - 1]}` : g.scores[0]}
            </td>
            <td className="py-2.5 pr-3 font-medium">{g.risk}</td>
            <td className="py-2.5 pr-3 tabular">{g.mortality}</td>
            <td className="py-2.5 text-ink-2">{g.care}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
