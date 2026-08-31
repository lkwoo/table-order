// UIKit: shared presentational components.
import React, { createContext, useCallback, useContext, useState } from 'react'
import type { OrderStatus } from './types'
import './ui.css'

// ---- Button ----
type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  block?: boolean
}
export function Button({ variant = 'primary', block, className = '', ...rest }: ButtonProps) {
  const cls = [
    'btn',
    variant !== 'primary' ? `btn--${variant}` : '',
    block ? 'btn--block' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return <button className={cls} {...rest} />
}

// ---- Badge ----
export function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`badge badge--${status}`}>{status}</span>
}

// ---- Modal ----
export function Modal({
  open,
  title,
  onClose,
  children,
  testId,
}: {
  open: boolean
  title?: string
  onClose?: () => void
  children: React.ReactNode
  testId?: string
}) {
  if (!open) return null
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} data-testid={testId}>
        {title && <h3 className="modal__title">{title}</h3>}
        {children}
      </div>
    </div>
  )
}

// ---- Spinner ----
export function Spinner() {
  return <div className="spinner" aria-label="loading" />
}

// ---- Toast ----
interface ToastMsg {
  id: number
  text: string
  kind: 'info' | 'success' | 'error'
}
interface ToastCtx {
  show: (text: string, kind?: ToastMsg['kind']) => void
}
const ToastContext = createContext<ToastCtx>({ show: () => {} })

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMsg[]>([])
  const show = useCallback((text: string, kind: ToastMsg['kind'] = 'info') => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, text, kind }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000)
  }, [])
  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast--${t.kind}`} data-testid="toast">
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}

// ---- Currency formatting ----
export function formatKRW(amount: number): string {
  return amount.toLocaleString('ko-KR') + '원'
}

// ---- Date formatting ----
export function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('ko-KR', { hour12: false })
}
