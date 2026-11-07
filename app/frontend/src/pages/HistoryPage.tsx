import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { ChevronLeft, ChevronRight, FileDown, History, LayoutGrid, List, RefreshCw, Search, Trash2, X } from 'lucide-react'
import { api, downloadFile, errorMessage, type HistoryPage as HistoryData, type ScanRecord } from '../lib/api'
import { useToast } from '../lib/contexts'
import { dateTime, pct, relativeTime } from '../lib/format'
import { forgetScans } from '../lib/scanSession'
import { ConfirmDialog, PageHeader, RiskBadge, Segmented, Spinner, VerdictBadge } from '../components/ui'

type LabelFilter = 'all' | 'PNEUMONIA' | 'NORMAL'
type ViewKind = 'grid' | 'list'
const PAGE_SIZE = 24
const SOURCE = { scan: 'Upload', sample: 'Sample', triage: 'Triage' } as const

function readView(): ViewKind {
  try {
    return localStorage.getItem('pneumoscan-history-view') === 'list' ? 'list' : 'grid'
  } catch {
    return 'grid'
  }
}

function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = window.setTimeout(() => setV(value), ms)
    return () => window.clearTimeout(t)
  }, [value, ms])
  return v
}

function patientName(s: ScanRecord) {
  return s.patient.name?.trim() || null
}

function RowActions({ scan, onDelete }: { scan: ScanRecord; onDelete: (s: ScanRecord) => void }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  return (
    <div className="flex items-center gap-0.5">
      <button
        type="button"
        className="btn btn-ghost btn-icon size-9"
        aria-label={`Download PDF report for ${scan.id}`}
        title="Download PDF report"
        disabled={busy}
        onClick={async () => {
          setBusy(true)
          try {
            await downloadFile(scan.report_url, `PneumoScan_Report_${scan.id}.pdf`)
            toast.push('success', 'Report downloaded', `PneumoScan_Report_${scan.id}.pdf`)
          } catch (err) {
            toast.push('error', 'Could not download the report', errorMessage(err))
          } finally {
            setBusy(false)
          }
        }}
      >
        {busy ? <Spinner /> : <FileDown className="size-4" aria-hidden />}
      </button>
      <button
        type="button"
        className="btn btn-ghost btn-icon size-9 hover:text-flag!"
        aria-label={`Delete scan ${scan.id}`}
        title="Delete scan"
        onClick={() => onDelete(scan)}
      >
        <Trash2 className="size-4" aria-hidden />
      </button>
    </div>
  )
}

export default function HistoryPage() {
  const toast = useToast()
  const [q, setQ] = useState('')
  const [label, setLabel] = useState<LabelFilter>('all')
  const [page, setPage] = useState(1)
  const [view, setView] = useState<ViewKind>(readView)
  const [data, setData] = useState<HistoryData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [toDelete, setToDelete] = useState<ScanRecord | null>(null)
  const [clearing, setClearing] = useState(false)
  const [busy, setBusy] = useState(false)
  const query = useDebounced(q.trim(), 250)

  const seq = useRef(0)
  const load = useCallback(async () => {
    const mine = ++seq.current
    setLoading(true)
    setError(null)
    try {
      const d = await api.history({ q: query, page, page_size: PAGE_SIZE, label: label === 'all' ? '' : label })
      if (mine !== seq.current) return
      if (d.items.length === 0 && page > 1 && d.total > 0) {
        setPage(d.pages)
        return
      }
      setData(d)
    } catch (err) {
      if (mine === seq.current) setError(errorMessage(err))
    } finally {
      if (mine === seq.current) setLoading(false)
    }
  }, [query, page, label])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    setPage(1)
  }, [query, label])

  const changeView = (v: ViewKind) => {
    setView(v)
    try {
      localStorage.setItem('pneumoscan-history-view', v)
    } catch {
      /* ignore */
    }
  }

  async function doDelete() {
    if (!toDelete) return
    setBusy(true)
    try {
      await api.deleteScan(toDelete.id)
      forgetScans([toDelete.id])
      toast.push('success', 'Scan deleted', toDelete.id)
      setToDelete(null)
      await load()
    } catch (err) {
      toast.push('error', 'Could not delete the scan', errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function doClear() {
    setBusy(true)
    try {
      const r = await api.clearHistory()
      forgetScans()
      toast.push('success', 'History cleared', `${r.deleted} scan${r.deleted === 1 ? '' : 's'} deleted.`)
      setClearing(false)
      setPage(1)
      await load()
    } catch (err) {
      toast.push('error', 'Could not clear the history', errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const filtered = query !== '' || label !== 'all'
  const items = data?.items ?? []

  return (
    <div>
      <PageHeader
        eyebrow="History · stored on this computer only"
        title="Scan history"
        actions={
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setClearing(true)}
            disabled={!data || (data.total === 0 && !filtered)}
          >
            <Trash2 className="size-4" aria-hidden /> Clear all
          </button>
        }
      >
        Every analysed X-ray with its result, patient details and notes. Open one to review it or download its report again.
      </PageHeader>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-3" aria-hidden />
          <input
            type="search"
            className="field pr-9 pl-9"
            placeholder="Search by name, patient ID, scan ID, notes…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Search scans"
            maxLength={200}
          />
          {q && (
            <button
              type="button"
              className="btn btn-ghost btn-icon absolute top-1/2 right-1 size-8 -translate-y-1/2"
              onClick={() => setQ('')}
              aria-label="Clear search"
            >
              <X className="size-4" aria-hidden />
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Segmented<LabelFilter>
            label="Filter by result"
            value={label}
            onChange={setLabel}
            options={[
              { value: 'all', label: 'All' },
              { value: 'PNEUMONIA', label: 'Pneumonia' },
              { value: 'NORMAL', label: 'Normal' },
            ]}
          />
          <Segmented<ViewKind>
            label="Layout"
            value={view}
            onChange={changeView}
            options={[
              { value: 'grid', label: <LayoutGrid className="size-4" aria-label="Grid view" />, title: 'Grid view' },
              { value: 'list', label: <List className="size-4" aria-label="List view" />, title: 'List view' },
            ]}
          />
        </div>
      </div>

      <div className="mt-6 min-h-[320px]" aria-busy={loading}>
        {error ? (
          <div className="card flex flex-col items-center gap-3 p-10 text-center">
            <p className="font-semibold">Could not load the history</p>
            <p className="max-w-md text-sm text-ink-2">{error}</p>
            <button type="button" className="btn btn-secondary btn-sm mt-2" onClick={() => void load()}>
              <RefreshCw className="size-3.5" aria-hidden /> Retry
            </button>
          </div>
        ) : !data ? (
          <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }, (_, i) => (
              <li key={i} className="skeleton h-[290px] rounded-[18px]" />
            ))}
          </ul>
        ) : items.length === 0 ? (
          <div className="card flex flex-col items-center px-6 py-14 text-center">
            <span className="flex size-12 items-center justify-center rounded-2xl bg-accent-soft text-accent">
              <History className="size-6" aria-hidden />
            </span>
            <h2 className="mt-4 text-xl font-[650]">{filtered ? 'No scans match' : 'No saved scans yet'}</h2>
            <p className="mt-1.5 max-w-sm text-ink-2">
              {filtered
                ? 'Try a different search or clear the filter.'
                : 'Analyse an X-ray on the Scan page and it will be saved here automatically.'}
            </p>
            {filtered ? (
              <button
                type="button"
                className="btn btn-secondary mt-5"
                onClick={() => {
                  setQ('')
                  setLabel('all')
                }}
              >
                Clear search and filter
              </button>
            ) : (
              <Link to="/" className="btn btn-primary mt-5">
                Scan an X-ray
              </Link>
            )}
          </div>
        ) : view === 'grid' ? (
          <ul className={`grid grid-cols-1 gap-4 min-[420px]:grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 ${loading ? 'opacity-60' : ''}`}>
            {items.map((s) => (
              <li key={s.id} className="card group flex flex-col overflow-hidden transition-shadow hover:shadow-2">
                <Link to={`/history/${s.id}`} className="block rounded-t-[17px] focus-visible:outline-offset-[-2px]">
                  <span className="relative block aspect-[4/3] overflow-hidden bg-film">
                    <img
                      src={s.images.thumb}
                      alt={`Chest X-ray thumbnail for scan ${s.id}`}
                      loading="lazy"
                      className="h-full w-full object-cover object-top opacity-90 transition-transform duration-300 group-hover:scale-[1.03]"
                    />
                    <span className="absolute top-2.5 left-2.5">
                      <VerdictBadge label={s.label} size="sm" />
                    </span>
                    {s.mode === 'mock' && (
                      <span className="absolute top-2.5 right-2.5 rounded-md bg-caution px-1.5 py-0.5 font-mono text-[0.6rem] font-medium text-white uppercase">
                        Demo
                      </span>
                    )}
                  </span>
                  <span className="block px-4 pt-3.5">
                    <span className="flex items-baseline justify-between gap-2">
                      <span className={`truncate font-semibold ${patientName(s) ? '' : 'text-ink-3'}`}>
                        {patientName(s) ?? 'Unnamed patient'}
                      </span>
                      <span className="shrink-0 font-mono text-[0.85rem] font-medium tabular">{pct(s.prob_pneumonia, 0)}</span>
                    </span>
                    <span className="mt-0.5 block truncate font-mono text-[0.72rem] text-ink-3">{s.id}</span>
                  </span>
                </Link>
                <div className="mt-auto flex items-center justify-between gap-2 px-4 pt-2 pb-2.5">
                  <span className="text-[0.78rem] text-ink-3" title={dateTime(s.created_at)}>
                    {relativeTime(s.created_at)} · {SOURCE[s.source] ?? 'Upload'}
                  </span>
                  <RowActions scan={s} onDelete={setToDelete} />
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className={`card relative overflow-x-auto ${loading ? 'opacity-60' : ''}`}>
            <table className="w-full min-w-[720px] text-left text-[0.92rem]">
              <thead className="border-b border-line text-[0.75rem] text-ink-3">
                <tr>
                  <th scope="col" className="py-3 pr-2 pl-4 font-medium">X-ray</th>
                  <th scope="col" className="px-2 py-3 font-medium">Patient</th>
                  <th scope="col" className="px-2 py-3 font-medium">Result</th>
                  <th scope="col" className="px-2 py-3 font-medium">Probability</th>
                  <th scope="col" className="px-2 py-3 font-medium">Risk</th>
                  <th scope="col" className="px-2 py-3 font-medium">Date</th>
                  <th scope="col" className="py-3 pr-4 pl-2 text-right font-medium">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((s) => (
                  <tr key={s.id} className="border-b border-line last:border-0 hover:bg-surface-2">
                    <td className="py-2 pr-2 pl-4">
                      <Link to={`/history/${s.id}`} className="block w-12 overflow-hidden rounded-lg bg-film" aria-label={`Open scan ${s.id}`}>
                        <img src={s.images.thumb} alt="" loading="lazy" className="aspect-square w-12 object-cover" />
                      </Link>
                    </td>
                    <td className="max-w-[240px] px-2 py-2">
                      <Link to={`/history/${s.id}`} className="block truncate font-semibold hover:underline">
                        {patientName(s) ?? <span className="text-ink-3">Unnamed patient</span>}
                      </Link>
                      <span className="block truncate font-mono text-[0.72rem] text-ink-3">{s.id}</span>
                    </td>
                    <td className="px-2 py-2">
                      <VerdictBadge label={s.label} size="sm" />
                    </td>
                    <td className="px-2 py-2 font-mono tabular">{pct(s.prob_pneumonia)}</td>
                    <td className="px-2 py-2">
                      <RiskBadge risk={s.risk_level} size="sm" />
                    </td>
                    <td className="px-2 py-2 whitespace-nowrap text-ink-2">{dateTime(s.created_at)}</td>
                    <td className="py-2 pr-3 pl-2">
                      <div className="flex justify-end">
                        <RowActions scan={s} onDelete={setToDelete} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {data && data.pages > 1 && (
        <nav className="mt-6 flex items-center justify-between gap-3" aria-label="Pagination">
          <p className="text-sm text-ink-3">
            {data.total} scans · page {data.page} of {data.pages}
          </p>
          <div className="flex gap-2">
            <button type="button" className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft className="size-4" aria-hidden /> Previous
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={page >= data.pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next <ChevronRight className="size-4" aria-hidden />
            </button>
          </div>
        </nav>
      )}
      {data && data.pages <= 1 && data.total > 0 && (
        <p className="mt-6 text-sm text-ink-3">
          {data.total} scan{data.total === 1 ? '' : 's'}
          {filtered ? ' match' : ' saved'}
        </p>
      )}

      <ConfirmDialog
        open={!!toDelete}
        title="Delete this scan?"
        body={
          <>
            Scan <span className="font-mono text-[0.9em]">{toDelete?.id}</span>
            {toDelete && patientName(toDelete) ? ` for ${patientName(toDelete)}` : ''} will be removed with its images and
            notes. This cannot be undone.
          </>
        }
        confirmLabel={busy ? 'Deleting…' : 'Delete scan'}
        busy={busy}
        onConfirm={() => void doDelete()}
        onClose={() => setToDelete(null)}
      />
      <ConfirmDialog
        open={clearing}
        title="Clear the whole history?"
        body="Every saved scan, with its images and notes, will be permanently deleted from this computer. This cannot be undone."
        confirmLabel={busy ? 'Clearing…' : 'Delete all scans'}
        busy={busy}
        onConfirm={() => void doClear()}
        onClose={() => setClearing(false)}
      />
    </div>
  )
}
