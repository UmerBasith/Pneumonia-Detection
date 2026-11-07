import { Link } from 'react-router'
import { ThoraxOutline } from '../components/Dropzone'

export default function NotFoundPage() {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center py-20 text-center">
      <ThoraxOutline className="h-40 text-ink-3 opacity-60" />
      <p className="eyebrow mt-6">Error 404</p>
      <h1 className="display mt-3 text-[2.6rem]">Nothing on this film.</h1>
      <p className="mt-3 text-ink-2">This page does not exist. Check the address or go back to scanning.</p>
      <Link to="/" className="btn btn-primary mt-7">
        Go to Scan
      </Link>
    </div>
  )
}
