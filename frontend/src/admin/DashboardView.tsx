import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiClient } from '../shared/api'
import type { DashboardCard } from '../shared/types'
import { Button, Spinner, StatusBadge, formatKRW, useToast } from '../shared/ui'
import { useAdminAuth } from './AdminAuthContext'
import { useDashboardStream } from './useDashboardStream'
import TableOrderDetailPanel from './TableOrderDetailPanel'
import TableSetupModal from './TableSetupModal'

// A2: real-time dashboard with table cards (grid), new-order highlight, SSE.
export default function DashboardView() {
  const { auth } = useAdminAuth()
  const toast = useToast()
  const [cards, setCards] = useState<DashboardCard[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<{ id: string; number: string } | null>(null)
  const [setupOpen, setSetupOpen] = useState(false)
  const [highlighted, setHighlighted] = useState<Set<string>>(new Set())
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({})

  const refetch = useCallback(() => {
    ApiClient.getDashboard()
      .then(setCards)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Highlight a table for 3s when a new order arrives (A2 / R8).
  const highlight = useCallback((data: any) => {
    const tableId: string | undefined = data?.table_id
    if (!tableId) return
    setHighlighted((prev) => new Set(prev).add(tableId))
    if (timers.current[tableId]) clearTimeout(timers.current[tableId])
    timers.current[tableId] = setTimeout(() => {
      setHighlighted((prev) => {
        const next = new Set(prev)
        next.delete(tableId)
        return next
      })
    }, 3000)
  }, [])

  const conn = useDashboardStream(auth?.token ?? null, refetch, highlight)

  useEffect(() => {
    refetch()
  }, [refetch])

  useEffect(() => {
    if (conn === 'offline') toast.show('연결이 끊겼습니다. 마지막 데이터를 표시합니다.', 'error')
  }, [conn, toast])

  return (
    <div>
      {conn === 'offline' && (
        <div className="offline-banner" data-testid="admin-offline-banner">
          오프라인 — 재연결 시 자동으로 최신 상태를 불러옵니다.
        </div>
      )}
      <div className="section-title">
        <h2 style={{ margin: 0 }}>실시간 주문 현황</h2>
        <Button onClick={() => setSetupOpen(true)} data-testid="open-table-setup-button">
          + 테이블 추가
        </Button>
      </div>

      {loading ? (
        <Spinner />
      ) : cards.length === 0 ? (
        <p className="muted">등록된 테이블이 없습니다. 테이블을 추가해주세요.</p>
      ) : (
        <div className="dashboard-grid">
          {cards.map((c) => (
            <div
              key={c.table_id}
              className={`card table-card ${highlighted.has(c.table_id) ? 'has-new' : ''}`}
              onClick={() => setSelected({ id: c.table_id, number: c.table_number })}
              data-testid={`table-card-${c.table_number}`}
            >
              <div className="table-card__header">
                <span className="table-card__number">테이블 {c.table_number}</span>
                <span className="table-card__total">{formatKRW(c.total_amount)}</span>
              </div>
              {c.recent_orders.length === 0 ? (
                <div className="muted" style={{ fontSize: 13 }}>
                  주문 없음
                </div>
              ) : (
                c.recent_orders.map((r, i) => (
                  <div className="preview-row" key={i}>
                    <span>
                      #{r.order_number} {r.summary}
                    </span>
                    <StatusBadge status={r.status} />
                  </div>
                ))
              )}
            </div>
          ))}
        </div>
      )}

      {selected && (
        <TableOrderDetailPanel
          tableId={selected.id}
          tableNumber={selected.number}
          open={!!selected}
          onClose={() => setSelected(null)}
          onMutated={refetch}
        />
      )}
      <TableSetupModal open={setupOpen} onClose={() => setSetupOpen(false)} onCreated={refetch} />
    </div>
  )
}
