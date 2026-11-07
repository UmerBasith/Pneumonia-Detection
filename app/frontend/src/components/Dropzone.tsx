import { useRef, useState, type DragEvent, type ReactNode } from 'react'
import { FolderOpen } from 'lucide-react'
import { ACCEPT } from '../lib/format'
import { FilmCorners } from './XrayViewer'

/** Line drawing of a thorax, shown faintly on the empty lightbox. */
export function ThoraxOutline({ className = '' }: { className?: string }) {
  const ribs = [0, 1, 2, 3, 4, 5, 6]
  return (
    <svg viewBox="0 0 400 420" className={className} fill="none" aria-hidden focusable="false">
      <g stroke="currentColor" strokeLinecap="round">
        {/* lungs */}
        <path d="M188 70c-40 6-92 60-104 150-8 60-4 118 14 140 22 18 62 10 82-6 10-40 10-120 8-284Z" strokeWidth="1.6" opacity="0.55" />
        <path d="M212 70c40 6 92 60 104 150 8 60 4 118-14 140-22 18-62 10-82-6-10-40-10-120-8-284Z" strokeWidth="1.6" opacity="0.55" />
        {/* trachea + spine */}
        <path d="M200 10v80M200 90l-20 34M200 90l20 34" strokeWidth="2" opacity="0.6" />
        <path d="M200 120v290" strokeWidth="6" opacity="0.18" />
        {/* clavicles */}
        <path d="M196 64c-30-14-74-16-118 2M204 64c30-14 74-16 118 2" strokeWidth="2.2" opacity="0.5" />
        {/* ribs */}
        {ribs.map((i) => {
          const y = 96 + i * 38
          const spread = 96 + i * 10
          return (
            <g key={i} strokeWidth="1.3" opacity={0.38 - i * 0.025}>
              <path d={`M194 ${y}c-30 4-${spread - 30} 22-${spread} ${52 + i * 3}`} />
              <path d={`M206 ${y}c30 4 ${spread - 30} 22 ${spread} ${52 + i * 3}`} />
            </g>
          )
        })}
        {/* heart shadow */}
        <path d="M206 210c34 6 62 40 58 92-26 18-58 14-74-6" strokeWidth="1.2" opacity="0.3" />
        {/* diaphragm */}
        <path d="M96 352c30-30 70-34 98-12M206 340c28-24 70-22 100 14" strokeWidth="1.6" opacity="0.45" />
      </g>
    </svg>
  )
}

export function Dropzone({
  onFiles,
  multiple = false,
  disabled = false,
  disabledReason,
  className = '',
  compact = false,
  children,
}: {
  onFiles: (files: File[]) => void
  multiple?: boolean
  disabled?: boolean
  disabledReason?: string
  className?: string
  compact?: boolean
  children?: ReactNode
}) {
  const input = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const depth = useRef(0)

  const open = () => {
    if (!disabled) input.current?.click()
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    depth.current = 0
    setOver(false)
    if (disabled) return
    const files = Array.from(e.dataTransfer.files ?? [])
    if (files.length) onFiles(multiple ? files : files.slice(0, 1))
  }

  return (
    <div
      className={`lightbox group transition-[box-shadow,border-color] duration-200 ${
        over ? 'border-film-glow! shadow-[0_0_0_4px_color-mix(in_srgb,var(--film-glow)_35%,transparent),var(--shadow-3)]' : ''
      } ${className}`}
      onDragEnter={(e) => {
        e.preventDefault()
        depth.current += 1
        if (!disabled) setOver(true)
      }}
      onDragOver={(e) => {
        e.preventDefault()
        e.dataTransfer.dropEffect = disabled ? 'none' : 'copy'
      }}
      onDragLeave={() => {
        depth.current = Math.max(0, depth.current - 1)
        if (depth.current === 0) setOver(false)
      }}
      onDrop={onDrop}
    >
      <input
        ref={input}
        type="file"
        accept={ACCEPT}
        multiple={multiple}
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={(e) => {
          const files = Array.from(e.target.files ?? [])
          e.target.value = ''
          if (files.length) onFiles(files)
        }}
      />
      <button
        type="button"
        onClick={open}
        disabled={disabled}
        aria-disabled={disabled}
        aria-label={
          disabled
            ? disabledReason ?? 'Upload unavailable'
            : multiple
              ? 'Choose chest X-ray files to add to the triage queue, or drop them here'
              : 'Choose a chest X-ray to analyse, or drop it here'
        }
        className={`relative flex w-full flex-col items-center justify-center text-center focus-visible:outline-offset-[-4px] disabled:cursor-not-allowed ${
          compact ? 'min-h-[200px] px-6 py-8' : 'min-h-[420px] px-6 py-12 lg:min-h-[500px]'
        }`}
      >
        {!compact && (
          <ThoraxOutline
            className={`pointer-events-none absolute inset-0 m-auto h-[86%] text-film-glow transition-all duration-500 ${
              over ? 'scale-[1.02] opacity-90' : 'opacity-50 group-hover:opacity-70'
            }`}
          />
        )}
        <span className="relative flex flex-col items-center">
          <span
            className={`flex size-14 items-center justify-center rounded-2xl border transition-colors ${
              over ? 'border-film-glow bg-film-glow/25 text-white' : 'border-white/15 bg-white/[0.06] text-film-ink'
            }`}
          >
            <FolderOpen className="size-6" aria-hidden />
          </span>
          <span className="mt-5 font-display text-[1.45rem] font-[620] tracking-[-0.02em] text-white">
            {disabled
              ? disabledReason ?? 'Upload unavailable'
              : over
                ? 'Release to analyse'
                : multiple
                  ? 'Drop X-rays for the queue'
                  : 'Drop a chest X-ray here'}
          </span>
          {!disabled && (
            <span className="mt-2 text-[0.95rem] text-film-ink-2">
              or <span className="font-medium text-film-ink underline decoration-film-glow/60 underline-offset-4">browse files</span>
              {!multiple && <> · paste with Ctrl+V</>}
            </span>
          )}
          <span className="film-annot mt-6">
            JPG · PNG · BMP · WEBP · TIFF · DICOM — up to 25 MB{multiple ? ' each · 50 files' : ''}
          </span>
        </span>
        {children}
      </button>
      {!compact && (
        <FilmCorners
          tl={<span>{disabled ? 'Lightbox off' : 'Lightbox ready'}</span>}
          tr={<span>PA / AP chest</span>}
          bl={<span>Stays on this computer</span>}
          br={<span>ResNet · Grad-CAM</span>}
        />
      )}
    </div>
  )
}
