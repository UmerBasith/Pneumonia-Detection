import { useEffect } from 'react'
import { api, type ModelInfo } from './api'
import { normaliseMetrics, type NormalisedMetrics } from './metrics'
import { createStore, useStore } from './store'

const cache = createStore<{ status: 'idle' | 'loading' | 'ready' | 'error'; info: ModelInfo | null; metrics: NormalisedMetrics | null }>({
  status: 'idle',
  info: null,
  metrics: null,
})

function load() {
  if (cache.get().status === 'loading' || cache.get().status === 'ready') return
  cache.set({ status: 'loading', info: null, metrics: null })
  api
    .modelInfo()
    .then((info) => cache.set({ status: 'ready', info, metrics: normaliseMetrics(info.metrics) }))
    .catch(() => cache.set({ status: 'error', info: null, metrics: null }))
}

/** Test-set metrics from models/metrics.json, fetched once and shared. */
export function useTestMetrics(): NormalisedMetrics | null {
  const s = useStore(cache)
  useEffect(() => load(), [])
  return s.metrics
}
