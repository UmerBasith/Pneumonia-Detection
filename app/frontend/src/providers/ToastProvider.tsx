import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { CircleAlert, CircleCheck, Info, X } from 'lucide-react'
import { ToastContext, type ToastItem, type ToastKind } from '../lib/contexts'

const ICONS = { success: CircleCheck, error: CircleAlert, info: Info }
const TONE: Record<ToastKind, string> = {
  success: 'text-clear',
  error: 'text-flag',
  info: 'text-accent',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const seq = useRef(0)

  const dismiss = useCallback((id: number) => {
    setItems((list) => list.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (kind: ToastKind, title: string, body?: string) => {
      seq.current += 1
      const id = seq.current
      setItems((list) => {
        const rest = list.filter((t) => !(t.title === title && t.body === body))
        return [...rest.slice(-3), { id, kind, title, body }]
      })
      window.setTimeout(() => dismiss(id), kind === 'error' ? 7000 : 4200)
    },
    [dismiss],
  )

  const value = useMemo(() => ({ push }), [push])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4 sm:inset-x-auto sm:right-5 sm:bottom-5 sm:items-end"
        aria-live="polite"
      >
        <AnimatePresence initial={false}>
          {items.map((t) => {
            const Icon = ICONS[t.kind]
            return (
              <motion.div
                key={t.id}
                layout
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.98, transition: { duration: 0.16 } }}
                transition={{ type: 'spring', stiffness: 420, damping: 34 }}
                role={t.kind === 'error' ? 'alert' : 'status'}
                className="card pointer-events-auto flex w-full max-w-sm items-start gap-3 p-3.5 pr-2 shadow-3"
              >
                <Icon className={`mt-0.5 size-5 shrink-0 ${TONE[t.kind]}`} aria-hidden />
                <div className="min-w-0 flex-1">
                  <p className="text-[0.92rem] leading-snug font-semibold">{t.title}</p>
                  {t.body && <p className="mt-0.5 text-sm leading-snug text-ink-2">{t.body}</p>}
                </div>
                <button
                  type="button"
                  onClick={() => dismiss(t.id)}
                  className="btn btn-ghost btn-icon size-8 shrink-0"
                  aria-label="Dismiss notification"
                >
                  <X className="size-4" aria-hidden />
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}
