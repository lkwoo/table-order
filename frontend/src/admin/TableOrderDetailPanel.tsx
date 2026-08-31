import { useCallback, useEffect, useState } from 'react'
import { ApiClient, ApiError } from '../shared/api'
import { ALLOWED_TRANSITIONS, type Order, type OrderStatus } from '../shared/types'
import { Button, Modal, Spinner, StatusBadge, formatKRW, formatTime, useToast } from '../shared/ui'
import OrderHistoryModal from './OrderHistoryModal'

// A3/A4/A6/A7: table detail panel — order list, status change (forward-only),
// delete (confirm), session end (confirm), and history.
export default function TableOrderDetailPanel({
  tableId,
  tableNumber,
  open,
  onClose,
  onMutated,
}: {
  tableId: string
  tableNumber: string
  open: boolean
  onClose: () => void
  onMutated: () => void
}) {
  const toast = useToast()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [endConfirm, setEndConfirm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Order | null>(null)

  const load = useCallback(() => {
    if (!open) return
    setLoading(true)
    ApiClient.getTableOrders(tableId)
      .then(setOrders)
      .catch(() => setOrders([]))
      .finally(() => setLoading(false))
  }, [open, tableId])

  useEffect(() => {
    load()
  }, [load])

  const changeStatus = async (order: Order, status: OrderStatus) => {
    try {
      await ApiClient.updateOrderStatus(order.id, status)
      toast.show(`#${order.order_number} → ${status}`, 'success')
      load()
      onMutated()
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : '상태 변경 실패', 'error')
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await ApiClient.deleteOrder(deleteTarget.id)
      toast.show(`#${deleteTarget.order_number} 주문이 삭제되었습니다.`, 'success')
      setDeleteTarget(null)
      load()
      onMutated()
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : '삭제 실패', 'error')
    }
  }

  const confirmEndSession = async () => {
    try {
      const res = await ApiClient.endSession(tableId)
      toast.show(`세션 종료 완료 (${res.archived_count}건 이력 이동)`, 'success')
      setEndConfirm(false)
      onMutated()
      onClose()
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : '세션 종료 실패', 'error')
    }
  }

  return (
    <>
      <Modal open={open} title={`테이블 ${tableNumber}`} onClose={onClose} testId="table-detail-panel">
        <div className="row" style={{ justifyContent: 'flex-end', gap: 8, marginBottom: 12 }}>
          <Button variant="secondary" onClick={() => setHistoryOpen(true)} data-testid="open-history-button">
            과거 내역
          </Button>
          <Button variant="danger" onClick={() => setEndConfirm(true)} data-testid="end-session-button">
            세션 종료
          </Button>
        </div>

        {loading ? (
          <Spinner />
        ) : orders.length === 0 ? (
          <p className="muted" data-testid="detail-no-orders">
            현재 주문이 없습니다.
          </p>
        ) : (
          orders.map((o) => (
            <div className="detail-order" key={o.id} data-testid={`detail-order-${o.order_number}`}>
              <div className="detail-order__head">
                <div className="row">
                  <strong>#{o.order_number}</strong>
                  <StatusBadge status={o.status} />
                </div>
                <span className="muted" style={{ fontSize: 13 }}>
                  {formatTime(o.created_at)}
                </span>
              </div>
              {o.items.map((it, i) => (
                <div className="preview-row" key={i}>
                  <span>
                    {it.menu_name} × {it.quantity}
                  </span>
                  <span>{formatKRW(it.subtotal)}</span>
                </div>
              ))}
              <div className="preview-row">
                <strong>합계</strong>
                <strong>{formatKRW(o.total_amount)}</strong>
              </div>

              {/* OrderStatusControl — forward-only transitions */}
              <div className="row" style={{ marginTop: 8, flexWrap: 'wrap' }}>
                {ALLOWED_TRANSITIONS[o.status].map((next) => (
                  <Button
                    key={next}
                    variant="secondary"
                    onClick={() => changeStatus(o, next)}
                    data-testid={`order-status-${o.order_number}-${next}`}
                  >
                    {next}(으)로 변경
                  </Button>
                ))}
                {/* OrderDeleteControl */}
                <Button
                  variant="ghost"
                  onClick={() => setDeleteTarget(o)}
                  data-testid={`order-delete-${o.order_number}`}
                >
                  삭제
                </Button>
              </div>
            </div>
          ))
        )}

        <div className="row" style={{ justifyContent: 'flex-end', marginTop: 14 }}>
          <Button variant="secondary" onClick={onClose} data-testid="detail-close-button">
            닫기
          </Button>
        </div>
      </Modal>

      {/* Delete confirmation */}
      <Modal
        open={!!deleteTarget}
        title="주문 삭제"
        onClose={() => setDeleteTarget(null)}
        testId="delete-confirm-modal"
      >
        <p>#{deleteTarget?.order_number} 주문을 삭제하시겠습니까?</p>
        <div className="row" style={{ justifyContent: 'flex-end' }}>
          <Button variant="secondary" onClick={() => setDeleteTarget(null)} data-testid="delete-cancel-button">
            취소
          </Button>
          <Button variant="danger" onClick={confirmDelete} data-testid="delete-confirm-button">
            삭제
          </Button>
        </div>
      </Modal>

      {/* SessionEndControl confirmation */}
      <Modal open={endConfirm} title="세션 종료" onClose={() => setEndConfirm(false)} testId="end-session-modal">
        <p>
          테이블 {tableNumber}의 세션을 종료하시겠습니까? 현재 주문은 과거 이력으로 이동되고 테이블이
          초기화됩니다.
        </p>
        <div className="row" style={{ justifyContent: 'flex-end' }}>
          <Button variant="secondary" onClick={() => setEndConfirm(false)} data-testid="end-session-cancel-button">
            취소
          </Button>
          <Button variant="danger" onClick={confirmEndSession} data-testid="end-session-confirm-button">
            종료
          </Button>
        </div>
      </Modal>

      <OrderHistoryModal
        tableId={tableId}
        tableNumber={tableNumber}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
      />
    </>
  )
}
