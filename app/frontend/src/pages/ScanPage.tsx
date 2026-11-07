import { useCallback, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowLeft, ChevronDown, ImageOff, Plus, ScanLine, ShieldCheck, Sparkles, UserRound } from 'lucide-react'
import { api, ApiError, errorMessage, type SampleItem } from '../lib/api'
import { useStatus, useToast } from '../lib/contexts'
import { canPreviewInBrowser, precheckFile } from '../lib/format'
import { ageError, EMPTY_PATIENT } from '../lib/patient'
import { scanSession, type ScanPhase } from '../lib/scanSession'
import { useStore } from '../lib/store'
import { useModelState } from '../lib/useModelState'
import { Dropzone } from '../components/Dropzone'
import { PatientFields } from '../components/PatientFields'
import { SampleGallery } from '../components/SampleGallery'
import { ScanningView } from '../components/ScanningView'
import { ScanResultView } from '../components/ScanResultView'
import { FilmCorners } from '../components/XrayViewer'

const MIN_SCAN_MS = 1100

function setPhase(s: ScanPhase) {
  scanSession.set((prev) => ({ ...prev, state: s }))
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

export function ScanPage() {
  const session = useStore(scanSession)
  const { state, patient } = session
  const toast = useToast()
  const { health, connection } = useStatus()
  const model = useModelState()
  const [detailsOpen, setDetailsOpen] = useState(() => Object.values(patient).some((v) => v.trim() !== ''))
  const busy = state.phase === 'scanning'
  const ready = connection === 'online' && !!health?.ready
  const previewRef = useRef<string | null>(null)
  const boxRef = useRef<HTMLDivElement>(null)

  const unavailable =
    connection === 'offline'
      ? 'Server offline'
      : !health
        ? 'Connecting to the server…'
        : health.status === 'error'
          ? 'The model failed to load'
          : !health.ready
            ? 'Model warming up…'
            : undefined

  const run = useCallback(
    async (file: File, opts: { sample?: SampleItem } = {}) => {
      if (scanSession.get().state.phase === 'scanning') return
      const bad = precheckFile(file)
      if (bad) {
        toast.push('error', 'This file cannot be analysed', bad)
        return
      }
      const p = scanSession.get().patient
      const aErr = ageError(p.age)
      if (aErr) {
        setDetailsOpen(true)
        toast.push('error', 'Check the patient details', aErr)
        return
      }
      if (previewRef.current) URL.revokeObjectURL(previewRef.current)
      const previewUrl = canPreviewInBrowser(file) ? URL.createObjectURL(file) : null
      previewRef.current = previewUrl
      setPhase({ phase: 'scanning', fileName: file.name, previewUrl })
      if (window.innerWidth < 1024) boxRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      else window.scrollTo({ top: 0, behavior: 'smooth' })
      const started = performance.now()
      try {
        const res = await api.predict(file, file.name, {
          patient: p,
          source: opts.sample ? 'sample' : 'scan',
          groundTruth: opts.sample?.ground_truth ?? null,
        })
        const wait = MIN_SCAN_MS - (performance.now() - started)
        if (wait > 0) await sleep(wait)
        if (opts.sample) {
          const id = opts.sample.id
          const truth = opts.sample.category === 'not_xray' ? 'not_xray' : opts.sample.ground_truth
          if (truth) scanSession.set((prev) => ({ ...prev, revealed: { ...prev.revealed, [id]: truth } }))
        }
        if (res.rejected) {
          setPhase({ phase: 'rejected', fileName: res.filename, previewUrl, check: res.xray_check })
        } else {
          setPhase({ phase: 'result', scan: res.scan })
          // patient details now live with the saved scan
          scanSession.set((prev) => ({ ...prev, patient: EMPTY_PATIENT }))
        }
      } catch (err) {
        setPhase({ phase: 'idle' })
        const title =
          err instanceof ApiError && err.code === 'warming_up' ? 'The model is still warming up' : 'The X-ray could not be analysed'
        toast.push('error', title, errorMessage(err))
      }
    },
    [toast],
  )

  const pickSample = useCallback(
    async (s: SampleItem) => {
      try {
        const res = await fetch(s.url)
        if (!res.ok) throw new Error('missing')
        const blob = await res.blob()
        await run(new File([blob], s.filename, { type: blob.type || 'image/jpeg' }), { sample: s })
      } catch {
        toast.push('error', 'Could not open this sample', 'Check that the sample_xrays folder is still in place.')
      }
    },
    [run, toast],
  )

  // Paste an image from the clipboard (Ctrl+V) while on the Scan page.
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const target = e.target as HTMLElement | null
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) return
      const item = Array.from(e.clipboardData?.items ?? []).find((i) => i.kind === 'file')
      const file = item?.getAsFile()
      if (!file) return
      e.preventDefault()
      if (!ready) {
        toast.push('info', 'Not ready yet', unavailable ?? 'Please wait a moment.')
        return
      }
      const ext = (file.type.split('/')[1] || 'png').replace('jpeg', 'jpg')
      const named = file.name && file.name !== 'image.png' ? file : new File([file], `pasted-image.${ext}`, { type: file.type })
      void run(named)
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [run, ready, toast, unavailable])

  const reset = () => setPhase({ phase: 'idle' })

  if (state.phase === 'result') {
    return (
      <ScanResultView
        key={state.scan.id}
        scan={state.scan}
        onUpdated={(s) => setPhase({ phase: 'result', scan: s })}
        actions={
          <button type="button" className="btn btn-secondary" onClick={reset}>
            <Plus className="size-4" aria-hidden />
            New scan
          </button>
        }
      />
    )
  }

  if (state.phase === 'rejected') {
    return (
      <div className="grid gap-6 pt-8 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <section className="lightbox" aria-label="Rejected image">
            <div className="relative h-[min(60vh,560px)] min-h-[320px]">
              <div className="absolute inset-x-6 top-12 bottom-12 flex items-center justify-center">
                {state.previewUrl ? (
                  <img src={state.previewUrl} alt="The uploaded image" className="h-full w-full object-contain opacity-70" />
                ) : (
                  <ImageOff className="size-10 text-film-ink-2" aria-hidden />
                )}
              </div>
              <FilmCorners tl={<span className="text-film-ink">Image check</span>} tr={<span>{state.fileName}</span>} bl={<span>Not analysed</span>} />
            </div>
          </section>
        </div>
        <motion.section
          className="card h-fit overflow-hidden lg:col-span-5"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          aria-labelledby="rej"
        >
          <div className="h-1.5 bg-caution" aria-hidden />
          <div className="p-6 sm:p-7">
            <p className="eyebrow">Image check</p>
            <h1 id="rej" className="mt-2 text-[1.75rem] font-[660]">
              This doesn’t look like a chest X-ray
            </h1>
            <p className="mt-3 text-ink-2">{state.check.reason}</p>
            <p className="mt-3 text-[0.95rem] text-ink-2">
              PneumoScan only analyses frontal chest X-rays. To avoid a misleading answer, it did not make a prediction and
              nothing was saved.
            </p>
            <dl className="mt-5 rounded-xl bg-surface-2 px-4 py-3 ring-1 ring-line">
              <dt className="text-[0.75rem] font-medium text-ink-3">Chest X-ray likeness score</dt>
              <dd className="mt-0.5 font-semibold tabular">{(state.check.score * 100).toFixed(0)} / 100</dd>
            </dl>
            <button type="button" className="btn btn-primary mt-6" onClick={reset}>
              <ArrowLeft className="size-4" aria-hidden /> Try another image
            </button>
          </div>
        </motion.section>
      </div>
    )
  }

  return (
    <div>
      <div className="grid items-start gap-8 pt-8 lg:grid-cols-12 lg:gap-10 lg:pt-12">
        {/* thesis */}
        <div className="lg:col-span-5 lg:pt-6">
          <p className="eyebrow flex items-center gap-2">
            <ScanLine className="size-3.5" aria-hidden /> Chest X-ray screening · ResNet + Grad-CAM
          </p>
          <h1 className="display mt-4 text-[2.7rem] sm:text-[3.6rem] xl:text-[4.1rem]">
            A second read for every chest X-ray.
          </h1>
          <p className="mt-5 max-w-md text-[1.08rem] text-ink-2">
            Drop a radiograph on the lightbox. A ResNet model estimates the chance of pneumonia in about a second, then
            shows which regions drove its answer.
          </p>
          <ul className="mt-7 space-y-3 text-[0.95rem] text-ink-2">
            <li className="flex gap-3">
              <Sparkles className="mt-0.5 size-[1.1rem] shrink-0 text-accent" aria-hidden />
              <span>
                <strong className="font-semibold text-ink">Explains itself.</strong> A Grad-CAM heatmap marks the evidence.
              </span>
            </li>
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-[1.1rem] shrink-0 text-accent" aria-hidden />
              <span>
                <strong className="font-semibold text-ink">Private by design.</strong> Runs offline; images never leave this
                computer.
              </span>
            </li>
          </ul>

          {/* optional patient details */}
          <div className="mt-8 rounded-2xl border border-line bg-surface shadow-1">
            <button
              type="button"
              className="flex w-full items-center gap-3 rounded-2xl px-4 py-3.5 text-left"
              aria-expanded={detailsOpen}
              aria-controls="patient-details"
              onClick={() => setDetailsOpen((v) => !v)}
            >
              <span className="flex size-8 items-center justify-center rounded-lg bg-accent-soft text-accent">
                <UserRound className="size-4" aria-hidden />
              </span>
              <span className="flex-1">
                <span className="block text-[0.95rem] font-semibold">Patient details</span>
                <span className="block text-[0.82rem] text-ink-3">Optional · printed on the PDF report</span>
              </span>
              <ChevronDown className={`size-4 text-ink-3 transition-transform ${detailsOpen ? 'rotate-180' : ''}`} aria-hidden />
            </button>
            <AnimatePresence initial={false}>
              {detailsOpen && (
                <motion.div
                  id="patient-details"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.22, ease: [0.2, 0.7, 0.3, 1] }}
                  className="overflow-hidden"
                >
                  <div className="border-t border-line px-4 pt-4 pb-5">
                    <PatientFields value={patient} onChange={(v) => scanSession.set((prev) => ({ ...prev, patient: v }))} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* the lightbox */}
        <div ref={boxRef} className="scroll-mt-20 lg:col-span-7">
          {busy && state.phase === 'scanning' ? (
            <ScanningView fileName={state.fileName} previewUrl={state.previewUrl} />
          ) : (
            <Dropzone
              onFiles={(files) => void run(files[0])}
              disabled={!ready}
              disabledReason={unavailable}
            />
          )}
          {!ready && connection === 'online' && (
            <p className="mt-3 text-center text-sm text-ink-3" role="status">
              {model.label}: {model.detail}
            </p>
          )}
        </div>
      </div>

      <SampleGallery onPick={(s) => void pickSample(s)} disabled={busy || !ready} />
    </div>
  )
}
