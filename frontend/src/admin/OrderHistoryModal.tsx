import { useCallback, useEffect, useState } from 'react'
import { ApiClient } from '../shared/api'
import type { HistoryOrder } from '../shared/types'
import { Button, Modal, Spinner, formatKRW, formatTime } from '../shared/ui'

type DateFilter = 'all' | 'today' | 'yesterday'

// A8: past order history for a table with date filtering.
export default function OrderHistoryModal({
  tableId,
  tableNumber,
  open,
  onClose,
}: {
  tableId: string
  tableNumber: string
  open: boolean
  onClose: () => void
}) {
  const [filter, setFilter] = useState<DateFilter>('all')
  const [history, setHistory] = useState<HistoryOrder[]>([])
  const [loading, setLoading] = useState(false)

  const load = useCallback(() => {
    if (!open) return
    setLoading(true)
    ApiClient.getHistory(tableId, filter)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false))
  }, [open, tableId, filter])

  useEffect(() => {
    load()
  }, [load])

  return (
    <Modal open={open} title={`테이블 ${tableNumber} 과거 내역`} onClose={onClose} testId="history-modal">
      <div className="row" style={{ marginBottom: 14 }}>
        {(['all', 'today', 'yesterday'] as DateFilter[]).map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'primary' : 'secondary'}
            onClick={() => setFilter(f)}
            data-testid={`history-filter-${f}`}
          >
            {f === 'all' ? '전체' : f === 'today' ? '오늘' : '어제'}
          </Button>
        ))}
      </div>

      {loading ? (
        <Spinner />
      ) : history.length === 0 ? (
        <p className="muted" data-testid="history-empty">
          주문 내역이 없습니다.
        </p>
      ) : (
        history.map((h, idx) => (
          <div className="detail-order" key={idx} data-testid={`history-item-${h.order_number}`}>
            <div className="detail-order__head">
              <strong>#{h.order_number}</strong>
              <span>{formatKRW(h.total_amount)}</span>
            </div>
            <div className="muted" style={{ fontSize: 13 }}>
              주문: {formatTime(h.ordered_at)}
              {h.completed_at ? ` · 완료: ${formatTime(h.completed_at)}` : ''}
            </div>
            {h.items.map((it, i) => (
              <div className="preview-row" key={i}>
                <span>
                  {it.menu_name} × {it.quantity}
                </span>
                <span>{formatKRW(it.subtotal)}</span>
              </div>
            ))}
          </div>
        ))
      )}

      <div className="row" style={{ justifyContent: 'flex-end', marginTop: 14 }}>
        <Button variant="secondary" onClick={onClose} data-testid="history-close-button">
          닫기
        </Button>
      </div>
    </Modal>
  )
}
