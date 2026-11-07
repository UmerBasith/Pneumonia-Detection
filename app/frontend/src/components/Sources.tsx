import { ExternalLink } from 'lucide-react'
import { SOURCES, type SourceId } from '../content/medical'

export function SourceList({ ids, title = 'Sources' }: { ids: SourceId[]; title?: string }) {
  return (
    <div className="mt-4 border-t border-line pt-3">
      <p className="text-[0.72rem] font-semibold tracking-[0.08em] text-ink-3 uppercase">{title}</p>
      <ul className="mt-1.5 space-y-1">
        {ids.map((id) => {
          const s = SOURCES[id]
          return (
            <li key={id} className="text-[0.8rem] leading-snug text-ink-3">
              <a
                href={s.url}
                target="_blank"
                rel="noreferrer noopener"
                className="group inline underline decoration-line-strong underline-offset-2 hover:text-ink hover:decoration-ink-3"
              >
                {s.publisher} — {s.title}
                <ExternalLink className="ml-1 inline size-3 align-[-1px] opacity-60 group-hover:opacity-100" aria-hidden />
                <span className="sr-only"> (opens in a new tab)</span>
              </a>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
