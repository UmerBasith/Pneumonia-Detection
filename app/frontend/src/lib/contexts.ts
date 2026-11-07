import { createContext, useContext } from 'react'
import type { Health } from './api'

export type Theme = 'light' | 'dark'

export interface ThemeCtx {
  theme: Theme
  toggle: () => void
}
export const ThemeContext = createContext<ThemeCtx | null>(null)
export function useTheme(): ThemeCtx {
  const v = useContext(ThemeContext)
  if (!v) throw new Error('useTheme must be used inside ThemeProvider')
  return v
}

export type Connection = 'connecting' | 'online' | 'offline'
export interface StatusCtx {
  health: Health | null
  connection: Connection
  refresh: () => void
}
export const StatusContext = createContext<StatusCtx | null>(null)
export function useStatus(): StatusCtx {
  const v = useContext(StatusContext)
  if (!v) throw new Error('useStatus must be used inside StatusProvider')
  return v
}

export type ToastKind = 'success' | 'error' | 'info'
export interface ToastItem {
  id: number
  kind: ToastKind
  title: string
  body?: string
}
export interface ToastCtx {
  push: (kind: ToastKind, title: string, body?: string) => void
}
export const ToastContext = createContext<ToastCtx | null>(null)
export function useToast(): ToastCtx {
  const v = useContext(ToastContext)
  if (!v) throw new Error('useToast must be used inside ToastProvider')
  return v
}
