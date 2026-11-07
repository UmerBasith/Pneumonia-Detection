import { Link } from 'react-router'
import { LogoMark } from './Logo'

export function Footer() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto grid max-w-[1240px] 2xl:max-w-[1400px] gap-6 px-4 py-10 text-sm text-ink-3 sm:px-6 md:grid-cols-[1fr_auto] md:items-end">
        <div className="flex items-start gap-3">
          <LogoMark className="size-7 shrink-0" />
          <div>
            <p className="font-medium text-ink-2">PneumoScan AI · Pneumonia Detection using ResNet</p>
            <p className="mt-1 max-w-xl">
              An educational decision-support tool, not a medical device. It does not replace a doctor, a radiologist or
              clinical tests. Everything runs on this computer; no image leaves it.
            </p>
          </div>
        </div>
        <p className="md:text-right">
          CSDX530 Deep Learning mini project · BSARCIST
          <br />
          <Link to="/about" className="font-medium text-ink-2 underline-offset-4 hover:underline">
            Umer Basith G · 230171601192
          </Link>
        </p>
      </div>
    </footer>
  )
}
