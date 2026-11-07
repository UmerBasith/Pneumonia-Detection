import { ExternalLink, GraduationCap } from 'lucide-react'
import { DISCLAIMER } from '../content/medical'
import { useStatus } from '../lib/contexts'
import { PageHeader } from '../components/ui'

const STACK = [
  ['Model', 'PyTorch · torchvision ResNet ensemble · Grad-CAM'],
  ['Backend', 'Python 3.11 · FastAPI · SQLite · pydicom · ReportLab'],
  ['Frontend', 'React 19 · TypeScript · Vite · Tailwind CSS · Motion'],
  ['Runs on', 'This computer only (offline), GPU when available'],
]

export default function AboutPage() {
  const { health } = useStatus()
  return (
    <div>
      <PageHeader eyebrow="About the project" title="Pneumonia Detection using ResNet">
        PneumoScan AI is a CAT-2 mini project for the Deep Learning course. It shows how a residual network can screen chest
        X-rays for pneumonia, explain its answer with Grad-CAM, and fit into a doctor’s workflow with triage, history,
        reports and a CURB-65 calculator.
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-12">
        <section className="card overflow-hidden lg:col-span-7" aria-labelledby="who-h">
          <div className="lightbox rounded-none border-0 px-6 py-7 shadow-none sm:px-8">
            <p className="film-annot">Submitted by</p>
            <h2 id="who-h" className="mt-2 font-display text-[2.2rem] font-[650] tracking-[-0.03em] text-white">
              Umer Basith G
            </h2>
            <p className="mt-1 font-mono text-[0.95rem] text-film-ink">RRN 230171601192</p>
          </div>
          <dl className="grid gap-px bg-line sm:grid-cols-2">
            {[
              ['Course', 'CSDX530 – Deep Learning'],
              ['Assessment', 'CAT-2 Mini Project'],
              ['Faculty', 'Mahalakshmi R, AP / CSE'],
              ['Institution', 'B.S. Abdur Rahman Crescent Institute of Science and Technology (BSARCIST)'],
            ].map(([k, v]) => (
              <div key={k} className="bg-surface px-6 py-4 sm:px-8">
                <dt className="text-[0.78rem] font-medium text-ink-3">{k}</dt>
                <dd className="mt-0.5 font-medium">{v}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="card p-6 sm:p-7 lg:col-span-5" aria-labelledby="stack-h">
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-xl bg-accent-soft text-accent">
              <GraduationCap className="size-[1.1rem]" aria-hidden />
            </span>
            <h2 id="stack-h" className="text-[1.2rem] font-[650]">
              Built with
            </h2>
          </div>
          <dl className="mt-4 divide-y divide-line">
            {STACK.map(([k, v]) => (
              <div key={k} className="py-3">
                <dt className="text-[0.78rem] font-medium text-ink-3">{k}</dt>
                <dd className="mt-0.5 text-[0.95rem]">{v}</dd>
              </div>
            ))}
          </dl>
          {health && (
            <p className="mt-2 font-mono text-[0.75rem] text-ink-3">
              App {health.app_version} · model {health.model_version ?? '–'} · {health.device ?? '–'}
            </p>
          )}
        </section>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="card p-6 sm:p-7" aria-labelledby="data-h">
          <h2 id="data-h" className="text-[1.2rem] font-[650]">
            Dataset credit
          </h2>
          <p className="mt-3 text-[0.95rem] text-ink-2">
            Kermany D, et al. <em>Labeled Optical Coherence Tomography (OCT) and Chest X-Ray Images for
            Classification</em>. Mendeley Data, version 2, 2018. Licensed under CC BY 4.0. Described in Kermany et al.,{' '}
            <em>Cell</em> 172(5):1122–1131.e9, 2018.
          </p>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-[0.88rem] font-medium">
            <a className="inline-flex items-center gap-1 text-accent hover:underline" href="https://doi.org/10.17632/rscbjbr9sj.2" target="_blank" rel="noreferrer noopener">
              Dataset DOI <ExternalLink className="size-3.5" aria-hidden />
            </a>
            <a className="inline-flex items-center gap-1 text-accent hover:underline" href="https://doi.org/10.1016/j.cell.2018.02.010" target="_blank" rel="noreferrer noopener">
              Paper DOI <ExternalLink className="size-3.5" aria-hidden />
            </a>
            <a className="inline-flex items-center gap-1 text-accent hover:underline" href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer noopener">
              CC BY 4.0 <ExternalLink className="size-3.5" aria-hidden />
            </a>
          </div>
        </section>
        <section className="card p-6 sm:p-7" aria-labelledby="disc-h">
          <h2 id="disc-h" className="text-[1.2rem] font-[650]">
            Disclaimer
          </h2>
          <p className="mt-3 text-[0.95rem] text-ink-2">{DISCLAIMER}</p>
          <p className="mt-3 text-[0.95rem] text-ink-2">
            Patient details, images and notes are stored only in a local database on this computer. Nothing is sent to the
            internet.
          </p>
        </section>
      </div>
    </div>
  )
}
