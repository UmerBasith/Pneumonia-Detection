import type { ReactNode } from 'react'
import { Ambulance, Baby, Bug, HeartPulse, Home, ScanSearch, ShieldPlus, Stethoscope, Thermometer, Users } from 'lucide-react'
import { LEARN, SOURCES, type SourceId } from '../content/medical'
import { SourceList } from '../components/Sources'
import { PageHeader } from '../components/ui'

const TOC = [
  ['emergency', 'Emergency signs'],
  ['symptoms', 'Symptoms'],
  ['children', 'Children'],
  ['causes', 'Causes'],
  ['risk', 'Who is at risk'],
  ['prevention', 'Prevention'],
  ['diagnosis', 'Diagnosis'],
  ['home', 'Care at home'],
  ['xray', 'On an X-ray'],
] as const

function Card({
  id,
  icon,
  title,
  children,
  sources,
  className = '',
}: {
  id: string
  icon: ReactNode
  title: string
  children: ReactNode
  sources: SourceId[]
  className?: string
}) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className={`card scroll-mt-24 p-6 sm:p-7 ${className}`}>
      <div className="flex items-center gap-3">
        <span className="flex size-9 items-center justify-center rounded-xl bg-accent-soft text-accent">{icon}</span>
        <h2 id={`${id}-h`} className="text-[1.25rem] font-[650]">
          {title}
        </h2>
      </div>
      <div className="mt-4 text-[0.97rem] text-ink-2">{children}</div>
      <SourceList ids={sources} />
    </section>
  )
}

function Bullets({ items }: { items: ReactNode[] }) {
  return (
    <ul className="space-y-2">
      {items.map((it, i) => (
        <li key={i} className="flex gap-2.5">
          <span className="mt-[0.6rem] size-1.5 shrink-0 rounded-full bg-ink-3" aria-hidden />
          <span>{it}</span>
        </li>
      ))}
    </ul>
  )
}

export default function LearnPage() {
  const L = LEARN
  return (
    <div>
      <PageHeader eyebrow="Learn · general health information from WHO, NHS, CDC and NIH" title="Pneumonia, explained simply.">
        <div className="space-y-3">
          {L.what.paragraphs.map((p) => (
            <p key={p}>{p}</p>
          ))}
        </div>
        <p className="mt-3 text-[0.82rem] text-ink-3">
          Sources: {L.what.sources.map((s) => SOURCES[s].publisher).join(' · ')}. Information only; it does not replace a doctor.
        </p>
      </PageHeader>

      {/* key numbers */}
      <section aria-label="Key statistics" className="grid grid-cols-2 gap-px overflow-hidden rounded-[18px] border border-line bg-line md:grid-cols-5">
        {L.stats.rows.map((r) => (
          <div key={r.fact} className="bg-surface p-5">
            <p className="font-display text-[2rem] leading-none font-[650] tracking-[-0.03em] tabular">{r.number}</p>
            <p className="mt-2 text-[0.85rem] leading-snug text-ink-2">{r.fact}</p>
            <p className="mt-2 font-mono text-[0.68rem] tracking-[0.04em] text-ink-3 uppercase">
              {SOURCES[r.source].publisher.replace('World Health Organization', 'WHO')}
              {r.year ? ` · ${r.year}` : ''}
            </p>
          </div>
        ))}
      </section>

      <nav aria-label="On this page" className="mt-8 flex flex-wrap gap-2">
        {TOC.map(([id, label]) => (
          <a
            key={id}
            href={`#${id}`}
            className="rounded-full border border-line bg-surface px-3 py-1.5 text-[0.85rem] font-medium text-ink-2 hover:border-line-strong hover:text-ink"
          >
            {label}
          </a>
        ))}
      </nav>

      {/* emergency */}
      <section
        id="emergency"
        aria-labelledby="emergency-h"
        className="mt-8 scroll-mt-24 overflow-hidden rounded-[18px] border border-flag/30 bg-flag-soft"
      >
        <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_1.2fr]">
          <div>
            <span className="flex size-10 items-center justify-center rounded-xl bg-flag text-white dark:text-[#1a0705]">
              <Ambulance className="size-5" aria-hidden />
            </span>
            <h2 id="emergency-h" className="mt-4 text-[1.7rem] font-[680] text-ink">
              Emergency warning signs — go to hospital now
            </h2>
            <p className="mt-2 text-ink-2">{L.emergency.call}</p>
            <p className="mt-4 font-display text-[2.4rem] leading-none font-[700] tracking-[-0.03em] text-flag">108 · 112</p>
            <p className="mt-1 text-[0.85rem] text-ink-2">Ambulance / national emergency number in India. Local practice varies by state.</p>
          </div>
          <div>
            <ul className="grid gap-2.5 sm:grid-cols-2">
              {L.emergency.items.map((it) => (
                <li key={it} className="rounded-xl bg-surface/80 px-4 py-3 text-[0.95rem] font-medium text-ink ring-1 ring-flag/15">
                  {it}
                </li>
              ))}
            </ul>
            <p className="mt-4 text-[0.92rem] font-semibold text-ink">{L.emergency.noDrive}</p>
            <p className="mt-2 text-[0.92rem] text-ink-2">{L.emergency.sameDay}</p>
          </div>
        </div>
        <div className="px-6 pb-5 sm:px-8">
          <SourceList ids={L.emergency.sources} />
        </div>
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card id="symptoms" icon={<Thermometer className="size-[1.1rem]" aria-hidden />} title="Symptoms in adults" sources={L.adultSymptoms.sources}>
          <Bullets items={L.adultSymptoms.items} />
        </Card>

        <Card id="children" icon={<Baby className="size-[1.1rem]" aria-hidden />} title="Signs in children (WHO)" sources={L.child.sources}>
          <p>
            <strong className="font-semibold text-ink">Common signs:</strong> {L.child.common}
          </p>
          <h3 className="mt-4 text-[0.95rem] font-semibold text-ink">Fast breathing means</h3>
          <table className="mt-2 w-full text-[0.9rem]">
            <tbody>
              {L.child.fastBreathing.map((r) => (
                <tr key={r.age} className="border-b border-line last:border-0">
                  <th scope="row" className="py-2 pr-4 text-left font-medium text-ink">
                    {r.age}
                  </th>
                  <td className="py-2 tabular">{r.limit}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3">{L.child.indrawing}</p>
          <div className="mt-4 rounded-xl bg-flag-soft p-4 ring-1 ring-flag/20">
            <h3 className="text-[0.95rem] font-semibold text-flag">General danger signs — take the child to a hospital immediately</h3>
            <div className="mt-2 text-ink">
              <Bullets items={L.child.danger} />
            </div>
          </div>
          <p className="mt-4 text-[0.88rem]">{L.child.classification}</p>
        </Card>

        <Card id="causes" icon={<Bug className="size-[1.1rem]" aria-hidden />} title="Common causes" sources={L.causes.sources}>
          <div className="space-y-4">
            {L.causes.rows.map((r) => (
              <div key={r.type}>
                <h3 className="font-semibold text-ink">{r.type}</h3>
                <p className="mt-0.5 text-[0.92rem]">{r.examples}</p>
                <p className="mt-1 text-[0.85rem] text-ink-3">{r.note}</p>
              </div>
            ))}
            <p className="text-[0.88rem]">{L.causes.footnote}</p>
          </div>
        </Card>

        <Card id="risk" icon={<Users className="size-[1.1rem]" aria-hidden />} title="Who is at higher risk?" sources={L.risk.sources}>
          <Bullets
            items={L.risk.items.map(([a, b]) => (
              <>
                <strong className="font-semibold text-ink">{a}</strong>
                {b ? ` — ${b}` : ''}
              </>
            ))}
          />
        </Card>

        <Card id="prevention" icon={<ShieldPlus className="size-[1.1rem]" aria-hidden />} title="Prevention" sources={L.prevention.sources}>
          <h3 className="font-semibold text-ink">Vaccines (ask your doctor which ones you need)</h3>
          <div className="mt-2">
            <Bullets
              items={L.prevention.vaccines.map(([a, b]) => (
                <>
                  <strong className="font-semibold text-ink">{a}</strong>
                  {b ? ` — ${b}` : ''}
                </>
              ))}
            />
          </div>
          <p className="mt-3 rounded-xl bg-accent-soft px-4 py-3 text-[0.9rem] text-ink">{L.prevention.whoNote}</p>
          <h3 className="mt-4 font-semibold text-ink">Everyday habits</h3>
          <div className="mt-2">
            <Bullets items={L.prevention.habits} />
          </div>
        </Card>

        <Card id="diagnosis" icon={<Stethoscope className="size-[1.1rem]" aria-hidden />} title="How doctors diagnose pneumonia" sources={L.diagnosis.sources}>
          <ol className="space-y-3">
            {L.diagnosis.steps.map(([a, b], i) => (
              <li key={a} className="flex gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-sunken font-mono text-[0.75rem] text-ink-2 ring-1 ring-line">
                  {i + 1}
                </span>
                <span>
                  <strong className="font-semibold text-ink">{a}</strong> — {b}
                </span>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-[0.88rem] text-ink-3">PneumoScan AI only looks at step 3, the chest X-ray. A doctor puts all the steps together.</p>
        </Card>

        <Card id="home" icon={<Home className="size-[1.1rem]" aria-hidden />} title="Care at home (always follow your doctor’s advice)" sources={L.homeCare.sources}>
          <Bullets items={L.homeCare.items} />
        </Card>

        <Card id="xray" icon={<ScanSearch className="size-[1.1rem]" aria-hidden />} title="How pneumonia looks on a chest X-ray" sources={L.xray.sources}>
          <p className="mb-3 text-[0.85rem] text-ink-3">For doctors and students.</p>
          <dl className="space-y-3">
            {L.xray.items.map(([a, b]) => (
              <div key={a}>
                <dt className="font-semibold text-ink">{a}</dt>
                <dd className="mt-0.5 text-[0.92rem]">{b}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 flex gap-2.5 rounded-xl bg-sunken px-4 py-3 text-[0.9rem]">
            <HeartPulse className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
            <span>
              <strong className="font-semibold text-ink">Remember:</strong> {L.xray.remember}
            </span>
          </p>
        </Card>
      </div>
    </div>
  )
}
