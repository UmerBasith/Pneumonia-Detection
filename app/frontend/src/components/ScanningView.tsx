import { useEffect, useState } from 'react'
import { Check } from 'lucide-react'
import { FilmCorners } from './XrayViewer'
import { ThoraxOutline } from './Dropzone'
import { Spinner } from './ui'

const STEPS = ['Checking that it is a chest X-ray', 'Reading the film with the ResNet model', 'Tracing the evidence with Grad-CAM']

export function ScanningView({ fileName, previewUrl }: { fileName: string; previewUrl: string | null }) {
  const [step, setStep] = useState(0)
  useEffect(() => {
    const a = window.setTimeout(() => setStep(1), 380)
    const b = window.setTimeout(() => setStep(2), 820)
    return () => {
      window.clearTimeout(a)
      window.clearTimeout(b)
    }
  }, [])

  return (
    <section className="lightbox" aria-label="Analysing X-ray" aria-busy="true">
      <div className="relative h-[min(68vh,620px)] min-h-[380px] overflow-hidden">
        <div className="absolute inset-x-6 top-12 bottom-12">
          {previewUrl ? (
            <img src={previewUrl} alt="" className="h-full w-full object-contain opacity-80 grayscale" />
          ) : (
            <ThoraxOutline className="m-auto h-full text-film-glow opacity-60" />
          )}
        </div>
        <div className="scan-sweep" aria-hidden />
        <div className="absolute inset-x-0 bottom-14 flex justify-center px-4">
          <ol
            className="w-full max-w-sm space-y-2 rounded-2xl border border-white/10 bg-[rgb(6_11_17/0.78)] p-4 backdrop-blur-md"
            aria-live="polite"
          >
            {STEPS.map((s, i) => {
              const done = i < step
              const active = i === step
              return (
                <li key={s} className={`flex items-center gap-3 text-[0.9rem] ${done || active ? 'text-film-ink' : 'text-film-ink-2/70'}`}>
                  <span
                    className={`flex size-5 shrink-0 items-center justify-center rounded-full ${
                      done ? 'bg-film-glow/30 text-white' : 'border border-white/15'
                    }`}
                  >
                    {done ? <Check className="size-3" aria-hidden /> : active ? <Spinner className="size-3.5 text-film-glow" /> : null}
                  </span>
                  {s}
                </li>
              )
            })}
          </ol>
        </div>
        <FilmCorners
          tl={<span className="text-film-ink">Analysing</span>}
          tr={<span className="block max-w-[46vw] truncate">{fileName}</span>}
          bl={<span>Local inference · no upload to the internet</span>}
        />
      </div>
    </section>
  )
}
