import { useId } from 'react'
import { Segmented } from './ui'
import { ageError, type PatientDraft } from '../lib/patient'

export function PatientFields({
  value,
  onChange,
  notesLabel = 'Doctor’s notes',
  showNotes = true,
}: {
  value: PatientDraft
  onChange: (v: PatientDraft) => void
  notesLabel?: string
  showNotes?: boolean
}) {
  const id = useId()
  const set = (k: keyof PatientDraft) => (v: string) => onChange({ ...value, [k]: v })
  const aErr = ageError(value.age)
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-6">
      <div className="sm:col-span-4">
        <label className="field-label" htmlFor={`${id}-name`}>
          Patient name
        </label>
        <input
          id={`${id}-name`}
          className="field"
          value={value.name}
          maxLength={120}
          autoComplete="off"
          placeholder="e.g. Priya Raman"
          onChange={(e) => set('name')(e.target.value)}
        />
      </div>
      <div className="sm:col-span-2">
        <label className="field-label" htmlFor={`${id}-age`}>
          Age <span className="font-normal text-ink-3">(years)</span>
        </label>
        <input
          id={`${id}-age`}
          className="field tabular"
          inputMode="numeric"
          value={value.age}
          maxLength={5}
          placeholder="e.g. 58"
          aria-invalid={!!aErr}
          aria-describedby={aErr ? `${id}-age-err` : undefined}
          onChange={(e) => set('age')(e.target.value)}
        />
        {aErr && (
          <p id={`${id}-age-err`} className="mt-1 text-[0.78rem] text-flag">
            {aErr}
          </p>
        )}
      </div>
      <div className="sm:col-span-3">
        <span className="field-label" id={`${id}-sex`}>
          Sex
        </span>
        <Segmented
          label="Sex"
          value={value.sex || 'none'}
          onChange={(v) => set('sex')(v === 'none' ? '' : v)}
          options={[
            { value: 'none', label: 'Not set' },
            { value: 'Female', label: 'Female' },
            { value: 'Male', label: 'Male' },
            { value: 'Other', label: 'Other' },
          ]}
        />
      </div>
      <div className="sm:col-span-3">
        <label className="field-label" htmlFor={`${id}-pid`}>
          Patient ID
        </label>
        <input
          id={`${id}-pid`}
          className="field font-mono text-[0.92rem]"
          value={value.patient_id}
          maxLength={64}
          autoComplete="off"
          placeholder="e.g. OP-2026-0142"
          onChange={(e) => set('patient_id')(e.target.value)}
        />
      </div>
      <div className="sm:col-span-6">
        <label className="field-label" htmlFor={`${id}-sym`}>
          Symptoms
        </label>
        <textarea
          id={`${id}-sym`}
          className="field"
          rows={2}
          maxLength={2000}
          value={value.symptoms}
          placeholder="e.g. Cough and fever for 4 days, short of breath on walking"
          onChange={(e) => set('symptoms')(e.target.value)}
        />
      </div>
      {showNotes && (
        <div className="sm:col-span-6">
          <label className="field-label" htmlFor={`${id}-notes`}>
            {notesLabel}
          </label>
          <textarea
            id={`${id}-notes`}
            className="field"
            rows={3}
            maxLength={5000}
            value={value.notes}
            placeholder="Findings, advice given, follow-up plan…"
            onChange={(e) => set('notes')(e.target.value)}
          />
        </div>
      )}
    </div>
  )
}
