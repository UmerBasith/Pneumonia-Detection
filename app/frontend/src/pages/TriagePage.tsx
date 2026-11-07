import { useMemo, useState } from 'react'
import { Link } from 'react-router'
import { AnimatePresence, motion } from 'motion/react'
import { AlertTriangle, ArrowUpRight, CircleSlash, Download, ListOrdered, Trash2 } from 'lucide-react'
import { api, errorMessage, saveBlob } from '../lib/api'
import { useStatus, useToast } from '../lib/contexts'
import { canPreviewInBrowser, fileSize, pct, precheckFile } from '../lib/format'
import { useStore } from '../lib/store'
import { triageQueue, type TriageItem } from '../lib/scanSession'
import { Dropzone } from '../components/Dropzone'
import { ConfirmDialog, PageHeader, RiskBadge, Segmented, Spinner, VerdictBadge } from '../components/ui'

type QueueItem = TriageItem
type Filter = 'all' | 'urgent' | 'pneumonia' | 'normal' | 'issues'

const MAX_PER_DROP = 50
const CONCURRENCY = 2
const queue = triageQueue
let seq = 0
let running = 0

function patch(key: number, p: Partial<QueueItem>) {
  queue.set((list) => list.map((it) => (it.key === key ? { ...it, ...p } : it)))
}

function pump() {
  while (running < CONCURRENCY) {
    const next = queue.get().find((it) => it.status === 'queued')
    if (!next || !next.file) return
    running += 1
    const file = next.file
    patch(next.key, { status: 'analysing' })
    api
      .predict(file, next.name, { source: 'triage' })
      .then((res) => {
        if (res.rejected) patch(next.key, { status: 'rejected', message: res.xray_check.reason, file: null })
        else patch(next.key, { status: 'done', scan: res.scan, file: null })
      })
      .catch((err) => patch(next.key, { status: 'error', message: errorMessage(err), file: null }))
      .finally(() => {
        running -= 1
        pump()
      })
  }
}

function isUrgent(it: QueueItem) {
  return it.status === 'done' && it.scan?.risk_level === 'High'
}

function sortQueue(list: QueueItem[]): QueueItem[] {
  const group = (it: QueueItem) =>
    it.status === 'done' ? 0 : it.status === 'analysing' ? 1 : it.status === 'queued' ? 2 : it.status === 'rejected' ? 3 : 4
  return [...list].sort((a, b) => {
    const g = group(a) - group(b)
    if (g !== 0) return g
    if (a.status === 'done' && b.status === 'done') return (b.scan?.prob_pneumonia ?? 0) - (a.scan?.prob_pneumonia ?? 0)
    return a.key - b.key
  })
}

function csvCell(v: unknown): string {
  const s = v === null || v === undefined ? '' : String(v)
  const safe = /^[=+\-@\t\r]/.test(s) ? `'${s}` : s // avoid spreadsheet formula injection
  return /[",\n\r]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe
}

function exportCsv(list: QueueItem[]) {
  const head = ['priority', 'file', 'scan_id', 'result', 'prob_pneumonia', 'risk_level', 'urgent', 'threshold', 'status', 'message', 'analysed_at', 'model_mode']
  let rank = 0
  const rows = list.map((it) => {
    const s = it.scan
    if (it.status === 'done') rank += 1
    return [
      it.status === 'done' ? rank : '',
      it.name,
      s?.id ?? '',
      s?.label ?? '',
      s ? s.prob_pneumonia.toFixed(4) : '',
      s?.risk_level ?? '',
      isUrgent(it) ? 'yes' : 'no',
      s ? s.threshold.toFixed(4) : '',
      it.status,
      it.message ?? '',
      s?.created_at ?? '',
      s?.mode ?? '',
    ]
  })
  const csv = '﻿' + [head, ...rows].map((r) => r.map(csvCell).join(',')).join('\r\n')
  const d = new Date()
  const stamp = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}_${String(d.getHours()).padStart(2, '0')}${String(d.getMinutes()).padStart(2, '0')}`
  saveBlob(new Blob([csv], { type: 'text/csv;charset=utf-8' }), `PneumoScan_Triage_${stamp}.csv`)
}

function StatusCell({ it }: { it: QueueItem }) {
  if (it.status === 'queued') return <span className="text-[0.85rem] text-ink-3">Queued</span>
  if (it.status === 'analysing')
    return (
      <span className="inline-flex items-center gap-2 text-[0.85rem] text-accent">
        <Spinner className="size-3.5" /> Analysing
      </span>
    )
  if (it.status === 'rejected')
    return (
      <span className="inline-flex items-start gap-1.5 text-[0.85rem] text-caution">
        <CircleSlash className="mt-0.5 size-3.5 shrink-0" aria-hidden />
        <span>
          Not a chest X-ray<span className="block text-[0.78rem] text-ink-3">{it.message}</span>
        </span>
      </span>
    )
  if (it.status === 'error')
    return (
      <span className="inline-flex items-start gap-1.5 text-[0.85rem] text-flag">
        <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden />
        <span>
          Failed<span className="block text-[0.78rem] text-ink-3">{it.message}</span>
        </span>
      </span>
    )
  return it.scan ? <VerdictBadge label={it.scan.label} size="sm" /> : null
}

export default function TriagePage() {
  const items = useStore(queue)
  const toast = useToast()
  const { health, connection } = useStatus()
  const [filter, setFilter] = useState<Filter>('all')
  const [confirmClear, setConfirmClear] = useState(false)
  const ready = connection === 'online' && !!health?.ready

  const sorted = useMemo(() => sortQueue(items), [items])
  const counts = useMemo(() => {
    const done = items.filter((i) => i.status === 'done')
    return {
      total: items.length,
      finished: items.filter((i) => i.status !== 'queued' && i.status !== 'analysing').length,
      urgent: items.filter(isUrgent).length,
      pneumonia: done.filter((i) => i.scan?.label === 'PNEUMONIA').length,
      normal: done.filter((i) => i.scan?.label === 'NORMAL').length,
      issues: items.filter((i) => i.status === 'rejected' || i.status === 'error').length,
    }
  }, [items])
  const working = counts.finished < counts.total

  const visible = sorted.filter((it) => {
    if (filter === 'urgent') return isUrgent(it)
    if (filter === 'pneumonia') return it.status === 'done' && it.scan?.label === 'PNEUMONIA'
    if (filter === 'normal') return it.status === 'done' && it.scan?.label === 'NORMAL'
    if (filter === 'issues') return it.status === 'rejected' || it.status === 'error'
    return true
  })

  function add(files: File[]) {
    let list = files
    if (list.length > MAX_PER_DROP) {
      toast.push('info', `Added the first ${MAX_PER_DROP} files`, `Add up to ${MAX_PER_DROP} X-rays at a time.`)
      list = list.slice(0, MAX_PER_DROP)
    }
    const fresh: QueueItem[] = []
    let skipped = 0
    for (const f of list) {
      const bad = precheckFile(f)
      seq += 1
      if (bad) {
        skipped += 1
        fresh.push({ key: seq, file: null, name: f.name, size: f.size, status: 'error', message: bad, preview: null })
      } else {
        fresh.push({
          key: seq,
          file: f,
          name: f.name,
          size: f.size,
          status: 'queued',
          preview: canPreviewInBrowser(f) ? URL.createObjectURL(f) : null,
        })
      }
    }
    queue.set((q) => [...q, ...fresh])
    if (skipped) toast.push('error', `${skipped} file${skipped > 1 ? 's' : ''} skipped`, 'Unsupported or too-large files are listed under Issues.')
    pump()
  }

  function clear() {
    for (const it of queue.get()) if (it.preview) URL.revokeObjectURL(it.preview)
    queue.set([])
    setFilter('all')
    setConfirmClear(false)
  }

  return (
    <div>
      <PageHeader
        eyebrow="Triage · doctor mode"
        title="Read the sickest first."
        actions={
          items.length > 0 && (
            <>
              <button type="button" className="btn btn-secondary" onClick={() => exportCsv(sorted)} disabled={counts.finished === 0}>
                <Download className="size-4" aria-hidden /> Export CSV
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setConfirmClear(true)} disabled={working}>
                <Trash2 className="size-4" aria-hidden /> Clear queue
              </button>
            </>
          )
        }
      >
        Drop a batch of chest X-rays. Each one is analysed and saved to History, and the queue re-orders itself so the most
        likely pneumonia cases rise to the top. High-risk results are flagged as urgent.
      </PageHeader>

      <Dropzone
        multiple
        compact
        onFiles={add}
        disabled={!ready}
        disabledReason={connection === 'offline' ? 'Server offline' : 'Model warming up…'}
      />

      {items.length > 0 && (
        <section className="mt-8" aria-labelledby="queue-heading">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <h2 id="queue-heading" className="text-[1.25rem] font-[650]">
                Queue
              </h2>
              <span className="font-mono text-[0.8rem] text-ink-3 tabular" aria-live="polite">
                {counts.finished}/{counts.total} analysed
              </span>
            </div>
            <div className="-mx-1 max-w-[calc(100%+0.5rem)] overflow-x-auto px-1 py-1">
            <Segmented<Filter>
              label="Filter queue"
              size="sm"
              value={filter}
              onChange={setFilter}
              options={[
                { value: 'all', label: `All ${counts.total}` },
                { value: 'urgent', label: `Urgent ${counts.urgent}` },
                { value: 'pneumonia', label: `Pneumonia ${counts.pneumonia}` },
                { value: 'normal', label: `Normal ${counts.normal}` },
                { value: 'issues', label: `Issues ${counts.issues}` },
              ]}
            />
            </div>
          </div>
          <div className="mt-3 h-1 overflow-hidden rounded-full bg-sunken" aria-hidden>
            <motion.div
              className="h-full rounded-full bg-accent"
              animate={{ width: `${counts.total ? (counts.finished / counts.total) * 100 : 0}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          <div className="card relative mt-4 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-[0.92rem]">
              <caption className="sr-only">Triage queue sorted by pneumonia probability, highest first</caption>
              <thead className="border-b border-line text-[0.75rem] text-ink-3">
                <tr>
                  <th scope="col" className="w-14 py-3 pl-4 font-medium">
                    <ListOrdered className="size-4" aria-label="Priority" />
                  </th>
                  <th scope="col" className="px-2 py-3 font-medium">X-ray</th>
                  <th scope="col" className="px-2 py-3 font-medium">Status</th>
                  <th scope="col" className="w-[28%] px-2 py-3 font-medium">Pneumonia probability</th>
                  <th scope="col" className="px-2 py-3 font-medium">Risk</th>
                  <th scope="col" className="py-3 pr-4 pl-2 text-right font-medium">
                    <span className="sr-only">Open</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence initial={false}>
                  {visible.map((it) => {
                    const urgent = isUrgent(it)
                    const rank = it.status === 'done' ? sorted.filter((x) => x.status === 'done').indexOf(it) + 1 : null
                    const thumb = it.scan?.images.thumb ?? it.preview
                    return (
                      <motion.tr
                        key={it.key}
                        layout="position"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className={`border-b border-line last:border-0 ${urgent ? 'bg-flag-soft/70 shadow-[inset_3px_0_0_var(--flag)]' : ''}`}
                      >
                        <td className="py-2.5 pl-4 font-mono text-[0.85rem] text-ink-3 tabular">
                          {rank ? String(rank).padStart(2, '0') : '–'}
                        </td>
                        <td className="max-w-[300px] px-2 py-2.5">
                          <div className="flex items-center gap-3">
                            <span className="block size-11 shrink-0 overflow-hidden rounded-lg bg-film ring-1 ring-film-line">
                              {thumb && <img src={thumb} alt="" className="h-full w-full object-cover" />}
                            </span>
                            <span className="min-w-0">
                              <span className="block truncate font-medium" title={it.name}>
                                {it.name}
                              </span>
                              <span className="flex items-center gap-2 text-[0.75rem] text-ink-3">
                                {fileSize(it.size)}
                                {urgent && (
                                  <span className="inline-flex items-center gap-1 rounded bg-flag px-1.5 py-px font-mono text-[0.62rem] font-medium tracking-[0.06em] text-white uppercase">
                                    <AlertTriangle className="size-3" aria-hidden /> Urgent
                                  </span>
                                )}
                              </span>
                            </span>
                          </div>
                        </td>
                        <td className="px-2 py-2.5">
                          <StatusCell it={it} />
                        </td>
                        <td className="px-2 py-2.5">
                          {it.scan ? (
                            <div className="flex items-center gap-3">
                              <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-sunken">
                                <div
                                  className={`absolute inset-y-0 left-0 rounded-full ${it.scan.label === 'PNEUMONIA' ? 'bg-flag' : 'bg-clear'}`}
                                  style={{ width: `${it.scan.prob_pneumonia * 100}%` }}
                                />
                                <div className="absolute inset-y-0 w-0.5 bg-ink/60" style={{ left: `${it.scan.threshold * 100}%` }} />
                              </div>
                              <span className="w-14 text-right font-mono text-[0.85rem] tabular">{pct(it.scan.prob_pneumonia)}</span>
                            </div>
                          ) : (
                            <span className="text-ink-3">–</span>
                          )}
                        </td>
                        <td className="px-2 py-2.5">{it.scan ? <RiskBadge risk={it.scan.risk_level} size="sm" /> : <span className="text-ink-3">–</span>}</td>
                        <td className="py-2.5 pr-4 pl-2 text-right">
                          {it.scan && (
                            <Link to={`/history/${it.scan.id}`} className="btn btn-ghost btn-sm" aria-label={`Open details for ${it.name}`}>
                              Open <ArrowUpRight className="size-3.5" aria-hidden />
                            </Link>
                          )}
                        </td>
                      </motion.tr>
                    )
                  })}
                </AnimatePresence>
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-ink-3">
                      Nothing in this filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[0.8rem] text-ink-3">
            The thin dark mark on each bar is the decision threshold. Urgent = high-risk band. Sorting is a reading-order aid,
            not a diagnosis.
          </p>
        </section>
      )}

      {items.length === 0 && (
        <p className="mt-6 text-center text-[0.95rem] text-ink-3">
          The queue is empty. Tip: select a whole folder of X-rays in the file picker with Ctrl+A.
        </p>
      )}

      <ConfirmDialog
        open={confirmClear}
        title="Clear the queue?"
        body="This empties the list on this page. The analysed scans stay saved in History."
        confirmLabel="Clear queue"
        danger={false}
        onConfirm={clear}
        onClose={() => setConfirmClear(false)}
      />
    </div>
  )
}
