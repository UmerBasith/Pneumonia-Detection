import type { Label, SampleItem, ScanRecord, XrayCheck } from './api'
import { createStore } from './store'
import { EMPTY_PATIENT, type PatientDraft } from './patient'

export type ScanPhase =
  | { phase: 'idle' }
  | { phase: 'scanning'; fileName: string; previewUrl: string | null }
  | { phase: 'result'; scan: ScanRecord }
  | { phase: 'rejected'; fileName: string; previewUrl: string | null; check: XrayCheck }

export interface ScanSession {
  state: ScanPhase
  patient: PatientDraft
  /** Sample X-rays that have been analysed: their ground truth may now be shown. */
  revealed: Record<string, Label | 'not_xray'>
}

export const scanSession = createStore<ScanSession>({
  state: { phase: 'idle' },
  patient: EMPTY_PATIENT,
  revealed: {},
})

export const samplesCache = createStore<{ status: 'idle' | 'loading' | 'ready' | 'error'; items: SampleItem[] }>({
  status: 'idle',
  items: [],
})

/* ------------------------------------------------------------------ Triage queue (lives here so History can tidy it) */
export type TriageStatus = 'queued' | 'analysing' | 'done' | 'rejected' | 'error'
export interface TriageItem {
  key: number
  file: File | null
  name: string
  size: number
  status: TriageStatus
  scan?: ScanRecord
  message?: string
  preview: string | null
}
export const triageQueue = createStore<TriageItem[]>([])

/**
 * Called after scans are deleted from History (ids) or the whole history is cleared (no ids):
 * the Scan page and the Triage queue must not keep showing results whose images are gone.
 */
export function forgetScans(ids?: string[]) {
  const gone = (id: string) => !ids || ids.includes(id)
  const s = scanSession.get().state
  if (s.phase === 'result' && gone(s.scan.id)) scanSession.set((prev) => ({ ...prev, state: { phase: 'idle' } }))
  const q = triageQueue.get()
  const keep = q.filter((it) => !(it.scan && gone(it.scan.id)))
  if (keep.length !== q.length) {
    for (const it of q) if (!keep.includes(it) && it.preview) URL.revokeObjectURL(it.preview)
    triageQueue.set(keep)
  }
}
