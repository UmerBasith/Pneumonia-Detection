import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { ArrowLeft, FileQuestion, Trash2 } from 'lucide-react'
import { api, ApiError, errorMessage, type ScanRecord } from '../lib/api'
import { useToast } from '../lib/contexts'
import { forgetScans } from '../lib/scanSession'
import { ScanResultView } from '../components/ScanResultView'
import { ConfirmDialog } from '../components/ui'

export default function ScanDetailPage() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const [scan, setScan] = useState<ScanRecord | null>(null)
  const [error, setError] = useState<{ notFound: boolean; message: string } | null>(null)
  const [confirm, setConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let alive = true
    setScan(null)
    setError(null)
    api
      .scan(id)
      .then((s) => alive && setScan(s))
      .catch((err) => {
        if (!alive) return
        setError({ notFound: err instanceof ApiError && err.status === 404, message: errorMessage(err) })
      })
    return () => {
      alive = false
    }
  }, [id])

  async function remove() {
    setDeleting(true)
    try {
      await api.deleteScan(id)
      forgetScans([id])
      toast.push('success', 'Scan deleted', id)
      nav('/history')
    } catch (err) {
      toast.push('error', 'Could not delete the scan', errorMessage(err))
      setDeleting(false)
      setConfirm(false)
    }
  }

  const back = (
    <Link to="/history" className="btn btn-ghost btn-sm -ml-2 mt-6">
      <ArrowLeft className="size-4" aria-hidden /> All scans
    </Link>
  )

  if (error) {
    return (
      <div>
        {back}
        <div className="mx-auto mt-16 max-w-md text-center">
          <FileQuestion className="mx-auto size-10 text-ink-3" aria-hidden />
          <h1 className="mt-4 text-2xl font-[650]">{error.notFound ? 'Scan not found' : 'Could not open this scan'}</h1>
          <p className="mt-2 text-ink-2">{error.notFound ? 'It may have been deleted from the history.' : error.message}</p>
          <Link to="/history" className="btn btn-primary mt-6">
            Go to history
          </Link>
        </div>
      </div>
    )
  }

  if (!scan) {
    return (
      <div aria-busy="true" aria-label="Loading scan">
        {back}
        <div className="mt-6 grid gap-6 lg:grid-cols-12">
          <div className="skeleton h-[min(68vh,620px)] rounded-[22px] lg:col-span-7" />
          <div className="skeleton h-[520px] rounded-[18px] lg:col-span-5" />
        </div>
      </div>
    )
  }

  return (
    <div>
      {back}
      <ScanResultView
        key={scan.id}
        scan={scan}
        onUpdated={setScan}
        actions={
          <button type="button" className="btn btn-secondary" onClick={() => setConfirm(true)}>
            <Trash2 className="size-4" aria-hidden /> Delete
          </button>
        }
      />
      <ConfirmDialog
        open={confirm}
        title="Delete this scan?"
        body={
          <>
            Scan <span className="font-mono text-[0.9em]">{scan.id}</span>, its images and notes will be removed from this
            computer. This cannot be undone.
          </>
        }
        confirmLabel={deleting ? 'Deleting…' : 'Delete scan'}
        busy={deleting}
        onConfirm={() => void remove()}
        onClose={() => setConfirm(false)}
      />
    </div>
  )
}
