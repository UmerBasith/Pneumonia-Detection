import type { ScanRecord } from './api'

export interface PatientDraft {
  name: string
  age: string
  sex: string
  patient_id: string
  symptoms: string
  notes: string
}

export const EMPTY_PATIENT: PatientDraft = { name: '', age: '', sex: '', patient_id: '', symptoms: '', notes: '' }

export function ageError(age: string): string | null {
  const s = age.trim()
  if (!s) return null
  const n = Number(s)
  if (!Number.isFinite(n) || !/^\d{1,3}(\.\d+)?$/.test(s)) return 'Enter the age in years, for example 45.'
  if (n < 0 || n > 130) return 'Age must be between 0 and 130.'
  return null
}

export function draftFromScan(scan: ScanRecord): PatientDraft {
  return {
    name: scan.patient.name ?? '',
    age: scan.patient.age === null || scan.patient.age === undefined ? '' : String(scan.patient.age),
    sex: scan.patient.sex ?? '',
    patient_id: scan.patient.patient_id ?? '',
    symptoms: scan.patient.symptoms ?? '',
    notes: scan.doctor_notes ?? '',
  }
}

export function sameDraft(a: PatientDraft, b: PatientDraft): boolean {
  return (Object.keys(a) as (keyof PatientDraft)[]).every((k) => a[k].trim() === b[k].trim())
}
