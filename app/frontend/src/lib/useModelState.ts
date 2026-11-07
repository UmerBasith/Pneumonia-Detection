import { useStatus } from './contexts'

export type Tone = 'ok' | 'warn' | 'demo' | 'down'

export function useModelState(): { tone: Tone; label: string; detail: string } {
  const { health, connection } = useStatus()
  if (connection === 'offline') return { tone: 'down', label: 'Server offline', detail: 'Start start.bat to use the app' }
  if (!health) return { tone: 'warn', label: 'Connecting', detail: 'Contacting the local server' }
  if (health.status === 'error') return { tone: 'down', label: 'Model error', detail: health.error ?? 'The model failed to load' }
  if (!health.ready) return { tone: 'warn', label: 'Warming up', detail: 'Loading the ResNet weights' }
  if (health.mode === 'mock') return { tone: 'demo', label: 'Demo mode', detail: 'Mock model, results are simulated' }
  return {
    tone: 'ok',
    label: 'Model ready',
    detail: `${health.model_version ?? 'ResNet'} on ${health.device ?? 'CPU'}`,
  }
}
