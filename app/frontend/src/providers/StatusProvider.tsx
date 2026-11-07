import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { api, type Health } from '../lib/api'
import { StatusContext, type Connection } from '../lib/contexts'

/** Polls /api/health: fast while the model warms up or the server is down, slow once ready. */
export function StatusProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<Health | null>(null)
  const [connection, setConnection] = useState<Connection>('connecting')
  const timer = useRef<number | undefined>(undefined)
  const alive = useRef(true)

  const poll = useCallback(async () => {
    window.clearTimeout(timer.current)
    const ctrl = new AbortController()
    const kill = window.setTimeout(() => ctrl.abort(), 4000)
    let next = 3000
    try {
      const h = await api.health(ctrl.signal)
      if (!alive.current) return
      setHealth(h)
      setConnection('online')
      next = h.ready ? 15000 : 1500
    } catch {
      if (!alive.current) return
      setConnection('offline')
      next = 3000
    } finally {
      window.clearTimeout(kill)
    }
    if (alive.current) timer.current = window.setTimeout(() => void poll(), next)
  }, [])

  useEffect(() => {
    alive.current = true
    void poll()
    return () => {
      alive.current = false
      window.clearTimeout(timer.current)
    }
  }, [poll])

  const refresh = useCallback(() => void poll(), [poll])
  const value = useMemo(() => ({ health, connection, refresh }), [health, connection, refresh])
  return <StatusContext.Provider value={value}>{children}</StatusContext.Provider>
}
