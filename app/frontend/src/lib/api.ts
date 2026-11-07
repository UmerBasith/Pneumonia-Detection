// Typed client for the PneumoScan FastAPI backend.

export type ModelMode = 'real' | 'mock'
export type Label = 'PNEUMONIA' | 'NORMAL'
export type RiskLevel = 'Low' | 'Moderate' | 'High'
export type ScanSource = 'scan' | 'sample' | 'triage'

export interface Health {
  status: 'ok' | 'warming_up' | 'error'
  ready: boolean
  mode: ModelMode | null
  device: string | null
  model_version: string | null
  mock_reason: string | null
  error: string | null
  app_version: string
}

export interface XrayCheck {
  is_xray: boolean
  score: number
  reason: string
}

export interface Patient {
  name: string
  age: number | null
  sex: string
  patient_id: string
  symptoms: string
}

export interface ScanImages {
  input: string
  overlay: string
  heatmap: string
  thumb: string
}

export interface ScanRecord {
  id: string
  created_at: string
  updated_at: string
  filename: string
  source: ScanSource
  mode: ModelMode
  label: Label
  prob_pneumonia: number
  confidence: number
  threshold: number
  risk_level: RiskLevel
  inference_ms: number
  model_version: string
  xray_check: XrayCheck
  patient: Patient
  doctor_notes: string
  ground_truth: Label | null
  width: number | null
  height: number | null
  images: ScanImages
  report_url: string
}

export type PredictResponse =
  | { rejected: false; saved: boolean; scan: ScanRecord }
  | { rejected: true; saved: false; filename: string; xray_check: XrayCheck }

export interface HistoryPage {
  items: ScanRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface SampleItem {
  id: string
  filename: string
  url: string
  thumb_url: string
  category: 'normal' | 'pneumonia' | 'not_xray'
  ground_truth: Label | null
  title: string
}

export interface FigureItem {
  name: string
  title: string
  url: string
}

export interface ModelInfo {
  mode: ModelMode | null
  ready: boolean
  model_version: string | null
  metrics: Record<string, unknown> | null
  model_card: Record<string, unknown> | null
  figures: FigureItem[]
}

export interface BatchItem {
  filename: string
  ok: boolean
  rejected: boolean
  error: { code: string; message: string } | null
  scan: ScanRecord | null
  xray_check: XrayCheck | null
}

export class ApiError extends Error {
  code: string
  status: number
  constructor(code: string, message: string, status: number) {
    super(message)
    this.code = code
    this.status = status
  }
}

const OFFLINE_MESSAGE =
  'Cannot reach the PneumoScan server. Make sure start.bat is still running, then try again.'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, init)
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError('offline', OFFLINE_MESSAGE, 0)
  }
  const type = res.headers.get('content-type') ?? ''
  if (!res.ok) {
    if (type.includes('application/json')) {
      const body: unknown = await res.json().catch(() => null)
      const e = (body as { error?: { code?: string; message?: string } } | null)?.error
      if (e?.message) throw new ApiError(e.code ?? 'error', e.message, res.status)
    }
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      throw new ApiError('offline', OFFLINE_MESSAGE, res.status)
    }
    throw new ApiError('http_' + res.status, `The server answered with an error (${res.status}). Please try again.`, res.status)
  }
  if (!type.includes('application/json')) {
    throw new ApiError('bad_response', 'The server sent an unexpected response. Restart start.bat and try again.', res.status)
  }
  return (await res.json()) as T
}

export interface PatientInput {
  name?: string
  age?: string
  sex?: string
  patient_id?: string
  symptoms?: string
  notes?: string
}

export const api = {
  health: (signal?: AbortSignal) => request<Health>('/api/health', { signal, cache: 'no-store' }),
  modelInfo: () => request<ModelInfo>('/api/model-info'),
  samples: () => request<{ items: SampleItem[] }>('/api/samples'),

  predict(
    file: Blob,
    filename: string,
    opts: { patient?: PatientInput; source?: ScanSource; groundTruth?: Label | null; signal?: AbortSignal } = {},
  ) {
    const fd = new FormData()
    fd.append('file', file, filename)
    const p = opts.patient ?? {}
    for (const [k, v] of Object.entries(p)) {
      if (typeof v === 'string' && v.trim() !== '') fd.append(k, v.trim())
    }
    if (opts.source) fd.append('source', opts.source)
    if (opts.groundTruth) fd.append('ground_truth', opts.groundTruth)
    return request<PredictResponse>('/api/predict', { method: 'POST', body: fd, signal: opts.signal })
  },

  batch(files: File[]) {
    const fd = new FormData()
    for (const f of files) fd.append('files', f, f.name)
    return request<{ items: BatchItem[]; count: number }>('/api/batch', { method: 'POST', body: fd })
  },

  history(params: { q?: string; page?: number; page_size?: number; label?: string; source?: string }) {
    const sp = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== '' && v !== null) sp.set(k, String(v))
    }
    return request<HistoryPage>('/api/history?' + sp.toString(), { cache: 'no-store' })
  },
  scan: (id: string) => request<ScanRecord>('/api/history/' + encodeURIComponent(id), { cache: 'no-store' }),
  updateScan: (id: string, body: Partial<Patient> & { doctor_notes?: string }) =>
    request<ScanRecord>('/api/history/' + encodeURIComponent(id), {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    }),
  deleteScan: (id: string) =>
    request<{ deleted: number }>('/api/history/' + encodeURIComponent(id), { method: 'DELETE' }),
  clearHistory: () => request<{ deleted: number }>('/api/history', { method: 'DELETE' }),
}

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error && err.message) return err.message
  return 'Something went wrong. Please try again.'
}

/** Download a server file (PDF) without leaving the page; surfaces server errors as ApiError. */
export async function downloadFile(url: string, filename: string): Promise<void> {
  let res: Response
  try {
    res = await fetch(url, { cache: 'no-store' })
  } catch {
    throw new ApiError('offline', OFFLINE_MESSAGE, 0)
  }
  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null)
    const e = (body as { error?: { code?: string; message?: string } } | null)?.error
    throw new ApiError(e?.code ?? 'error', e?.message ?? 'Could not create the report. Please try again.', res.status)
  }
  const blob = await res.blob()
  saveBlob(blob, filename)
}

export function saveBlob(blob: Blob, filename: string) {
  const href = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(href), 4000)
}
