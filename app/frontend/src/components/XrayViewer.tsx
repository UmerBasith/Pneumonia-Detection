import { useCallback, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type ReactNode } from 'react'
import { ImageOff, Maximize2, Minus, Plus } from 'lucide-react'
import type { ScanImages } from '../lib/api'
import { Segmented } from './ui'

type ViewMode = 'original' | 'heatmap' | 'split'
interface View {
  z: number
  x: number
  y: number
}
const MIN_Z = 1
const MAX_Z = 6
const IDENTITY: View = { z: 1, x: 0, y: 0 }

function clampView(v: View, w: number, h: number): View {
  const z = Math.min(MAX_Z, Math.max(MIN_Z, v.z))
  const mx = ((z - 1) * w) / 2
  const my = ((z - 1) * h) / 2
  return { z, x: Math.min(mx, Math.max(-mx, v.x)), y: Math.min(my, Math.max(-my, v.y)) }
}

/** Corner annotations in the style of a radiology viewer. */
export function FilmCorners({ tl, tr, bl, br }: { tl?: ReactNode; tr?: ReactNode; bl?: ReactNode; br?: ReactNode }) {
  return (
    <>
      <span className="crop-mark tl" aria-hidden />
      <span className="crop-mark tr" aria-hidden />
      <span className="crop-mark bl" aria-hidden />
      <span className="crop-mark br" aria-hidden />
      {tl && <div className="film-annot pointer-events-none absolute top-4 left-6 z-10">{tl}</div>}
      {tr && <div className="film-annot pointer-events-none absolute top-4 right-6 z-10 text-right">{tr}</div>}
      {bl && <div className="film-annot pointer-events-none absolute bottom-4 left-6 z-10">{bl}</div>}
      {br && <div className="film-annot pointer-events-none absolute right-6 bottom-4 z-10 text-right">{br}</div>}
    </>
  )
}

function HeatLegend() {
  return (
    <span className="flex items-center gap-2">
      <span>Low</span>
      <span
        className="inline-block h-1.5 w-16 rounded-full"
        style={{ background: 'linear-gradient(90deg,#00007f,#0000ff,#00ffff,#ffff00,#ff0000,#7f0000)' }}
        aria-hidden
      />
      <span>High influence</span>
    </span>
  )
}

function Pane({
  view,
  images,
  showHeat,
  opacity,
  caption,
  onFailed,
}: {
  view: View
  images: ScanImages
  showHeat: boolean
  opacity: number
  caption?: string
  onFailed: () => void
}) {
  const [loaded, setLoaded] = useState(false)
  const style: CSSProperties = {
    transform: `translate3d(${view.x}px, ${view.y}px, 0) scale(${view.z})`,
    transition: 'transform 90ms ease-out',
  }
  return (
    <div className="relative h-full min-w-0 flex-1 overflow-hidden">
      {!loaded && <div className="absolute inset-[14%] animate-pulse rounded-xl bg-white/[0.04]" aria-hidden />}
      <div className="absolute inset-0 will-change-transform" style={style}>
        <img
          src={images.input}
          alt="Chest X-ray as analysed by the model"
          draggable={false}
          onLoad={() => setLoaded(true)}
          onError={onFailed}
          className={`absolute inset-0 h-full w-full object-contain transition-opacity duration-300 select-none ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
        {showHeat && (
          <img
            src={images.heatmap}
            alt="Grad-CAM heatmap showing the regions that most influenced the result"
            draggable={false}
            onError={onFailed}
            className="absolute inset-0 h-full w-full object-contain select-none"
            style={{ opacity, mixBlendMode: 'normal' }}
          />
        )}
      </div>
      {caption && (
        <span className="film-annot pointer-events-none absolute top-4 left-1/2 z-10 -translate-x-1/2 rounded-md bg-black/40 px-2 py-0.5 text-film-ink">
          {caption}
        </span>
      )}
    </div>
  )
}

export function XrayViewer({
  images,
  scanId,
  createdAt,
  modelVersion,
  height = 'h-[420px] sm:h-[min(68vh,620px)] sm:min-h-[340px]',
}: {
  images: ScanImages
  scanId: string
  createdAt: string
  modelVersion: string
  height?: string
}) {
  const [mode, setMode] = useState<ViewMode>('heatmap')
  const [opacity, setOpacity] = useState(0.6)
  const [view, setView] = useState<View>(IDENTITY)
  const [failed, setFailed] = useState(false)
  const stage = useRef<HTMLDivElement>(null)
  const pointers = useRef(new Map<number, { x: number; y: number }>())
  const drag = useRef<{ x: number; y: number; vx: number; vy: number; dist?: number; z?: number } | null>(null)

  // Reset zoom when the scan changes.
  useEffect(() => {
    setView(IDENTITY)
    setFailed(false)
  }, [scanId])

  const paneSize = useCallback(() => {
    const el = stage.current
    if (!el) return { w: 1, h: 1, cx: 0, cy: 0, left: 0, top: 0 }
    const r = el.getBoundingClientRect()
    const split = mode === 'split' && el.clientWidth > 0
    const w = split ? r.width / 2 : r.width
    return { w, h: r.height, left: r.left, top: r.top, cx: w / 2, cy: r.height / 2 }
  }, [mode])

  const zoomAt = useCallback(
    (factor: number, clientX?: number, clientY?: number) => {
      setView((v) => {
        const { w, h, left, top, cx, cy } = paneSize()
        const nz = Math.min(MAX_Z, Math.max(MIN_Z, v.z * factor))
        let sx = 0
        let sy = 0
        if (clientX !== undefined && clientY !== undefined) {
          let px = clientX - left
          if (mode === 'split' && px > w) px -= w
          sx = px - cx
          sy = clientY - top - cy
        }
        const nx = sx - (nz * (sx - v.x)) / v.z
        const ny = sy - (nz * (sy - v.y)) / v.z
        return clampView({ z: nz, x: nx, y: ny }, w, h)
      })
    },
    [paneSize, mode],
  )

  // Wheel zoom needs a non-passive listener to stop the page from scrolling.
  useEffect(() => {
    const el = stage.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      // Ctrl + wheel (and trackpad pinch, which Chrome reports as Ctrl + wheel) zooms; a plain wheel scrolls the page.
      if (!e.ctrlKey && !e.metaKey) return
      if (Math.abs(e.deltaY) < 0.5) return
      e.preventDefault()
      zoomAt(Math.min(1.25, Math.max(0.8, Math.exp(-e.deltaY * 0.004))), e.clientX, e.clientY)
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [zoomAt])

  const onPointerDown = (e: PointerEvent) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
    const pts = [...pointers.current.values()]
    if (pts.length === 2) {
      const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y)
      drag.current = { x: 0, y: 0, vx: view.x, vy: view.y, dist, z: view.z }
    } else {
      drag.current = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y }
    }
  }
  const onPointerMove = (e: PointerEvent) => {
    if (!pointers.current.has(e.pointerId) || !drag.current) return
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    const { w, h } = paneSize()
    const pts = [...pointers.current.values()]
    const d = drag.current
    if (pts.length >= 2 && d.dist && d.z) {
      const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y)
      setView((v) => clampView({ ...v, z: (d.z as number) * (dist / (d.dist as number)) }, w, h))
      return
    }
    if (view.z <= 1) return
    setView(clampView({ z: view.z, x: d.vx + (e.clientX - d.x), y: d.vy + (e.clientY - d.y) }, w, h))
  }
  const onPointerUp = (e: PointerEvent) => {
    pointers.current.delete(e.pointerId)
    if (pointers.current.size === 0) drag.current = null
    else {
      const [p] = [...pointers.current.values()]
      drag.current = { x: p.x, y: p.y, vx: view.x, vy: view.y }
    }
  }

  const onKeyDown = (e: KeyboardEvent) => {
    const { w, h } = paneSize()
    const step = 40
    if (e.key === '+' || e.key === '=') zoomAt(1.25)
    else if (e.key === '-' || e.key === '_') zoomAt(1 / 1.25)
    else if (e.key === '0') setView(IDENTITY)
    else if (e.key === 'ArrowLeft') setView((v) => clampView({ ...v, x: v.x + step }, w, h))
    else if (e.key === 'ArrowRight') setView((v) => clampView({ ...v, x: v.x - step }, w, h))
    else if (e.key === 'ArrowUp') setView((v) => clampView({ ...v, y: v.y + step }, w, h))
    else if (e.key === 'ArrowDown') setView((v) => clampView({ ...v, y: v.y - step }, w, h))
    else return
    e.preventDefault()
  }

  const date = new Date(createdAt)
  const dateText = Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()
  const timeText = Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  const heatVisible = mode !== 'original'

  return (
    <section className="lightbox flex flex-col" aria-label="X-ray viewer">
      {/* toolbar */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-film-line px-4 py-3 sm:px-5">
        <Segmented<ViewMode>
          tone="film"
          size="sm"
          label="Image view"
          value={mode}
          onChange={(m) => {
            setMode(m)
            setView(IDENTITY)
          }}
          options={[
            { value: 'original', label: 'Original' },
            { value: 'heatmap', label: 'Heatmap' },
            { value: 'split', label: 'Side by side' },
          ]}
        />
        <label
          className={`flex min-w-[170px] flex-1 items-center gap-3 text-[0.78rem] text-film-ink-2 transition-opacity sm:max-w-[260px] ${
            heatVisible ? '' : 'pointer-events-none opacity-40'
          }`}
        >
          <span className="whitespace-nowrap">Heatmap</span>
          <input
            type="range"
            min={0}
            max={100}
            step={1}
            value={Math.round(opacity * 100)}
            disabled={!heatVisible}
            onChange={(e) => setOpacity(Number(e.target.value) / 100)}
            className="range"
            style={{ '--val': `${Math.round(opacity * 100)}%` } as CSSProperties}
            aria-label="Heatmap opacity"
            aria-valuetext={`${Math.round(opacity * 100)} percent`}
          />
          <span className="w-9 text-right font-mono text-film-ink tabular">{Math.round(opacity * 100)}%</span>
        </label>
        <div className="ml-auto flex items-center gap-1">
          <button
            type="button"
            className="btn btn-icon size-8 text-film-ink-2 hover:bg-white/10 hover:text-white"
            onClick={() => zoomAt(1 / 1.25)}
            disabled={view.z <= MIN_Z}
            aria-label="Zoom out"
          >
            <Minus className="size-4" aria-hidden />
          </button>
          <span className="w-12 text-center font-mono text-[0.78rem] text-film-ink tabular" aria-live="polite">
            {Math.round(view.z * 100)}%
          </span>
          <button
            type="button"
            className="btn btn-icon size-8 text-film-ink-2 hover:bg-white/10 hover:text-white"
            onClick={() => zoomAt(1.25)}
            disabled={view.z >= MAX_Z}
            aria-label="Zoom in"
          >
            <Plus className="size-4" aria-hidden />
          </button>
          <button
            type="button"
            className="btn btn-icon size-8 text-film-ink-2 hover:bg-white/10 hover:text-white"
            onClick={() => setView(IDENTITY)}
            disabled={view.z === 1}
            aria-label="Reset zoom"
            title="Reset zoom (0)"
          >
            <Maximize2 className="size-4" aria-hidden />
          </button>
        </div>
      </div>

      {/* stage */}
      <div
        ref={stage}
        tabIndex={0}
        role="img"
        aria-label="Chest X-ray with Grad-CAM heatmap. Plus and minus zoom, arrow keys pan, 0 resets."
        title="Double-click or Ctrl + scroll to zoom, drag to move"
        onKeyDown={onKeyDown}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={(e) => (view.z > 1 ? setView(IDENTITY) : zoomAt(2.2, e.clientX, e.clientY))}
        className={`relative flex touch-none rounded-b-[21px] focus-visible:outline-offset-[-3px] ${height} ${
          view.z > 1 ? 'cursor-grab active:cursor-grabbing' : 'cursor-zoom-in'
        }`}
      >
        {failed ? (
          <div className="m-auto flex flex-col items-center gap-2 px-6 text-center text-film-ink-2">
            <ImageOff className="size-8" aria-hidden />
            <p className="text-sm">The images for this scan could not be loaded. They may have been deleted.</p>
          </div>
        ) : (
          <div className="absolute inset-x-3 top-12 bottom-12 flex gap-2 sm:inset-x-6">
            {mode === 'split' ? (
              <>
                <Pane view={view} images={images} showHeat={false} opacity={0} caption="Original" onFailed={() => setFailed(true)} />
                <div className="w-px self-stretch bg-film-line" aria-hidden />
                <Pane view={view} images={images} showHeat opacity={opacity} caption="Grad-CAM" onFailed={() => setFailed(true)} />
              </>
            ) : (
              <Pane view={view} images={images} showHeat={mode === 'heatmap'} opacity={opacity} onFailed={() => setFailed(true)} />
            )}
          </div>
        )}
        <FilmCorners
          tl={
            <>
              <span className="text-film-ink">PneumoScan AI</span>
              <br />
              {scanId}
            </>
          }
          tr={
            <>
              {dateText}
              <br />
              {timeText}
            </>
          }
          bl={heatVisible ? <HeatLegend /> : <span>Chest · as analysed</span>}
          br={<span className="hidden sm:inline">{modelVersion}</span>}
        />
      </div>
    </section>
  )
}
