import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiClient } from '../shared/api'
import type { Order } from '../shared/types'
import { Button, Spinner, StatusBadge, formatKRW, formatTime } from '../shared/ui'
import { useCustomerAuth } from './CustomerAuthContext'
import { useOrderStream } from './useOrderStream'

// C11/C12: current-session order history with live status via SSE.
export default function OrderHistoryView() {
  const { auth } = useCustomerAuth()
  const navigate = useNavigate()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  const refetch = useCallback(() => {
    ApiClient.getOrders()
      .then(setOrders)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    refetch()
  }, [refetch])

  const conn = useOrderStream(auth?.token ?? null, refetch)

  return (
    <div className="customer-shell">
      {conn === 'offline' && (
        <div className="offline-banner" data-testid="customer-offline-banner">
          연결이 끊겼습니다. 재연결을 시도 중입니다...
        </div>
      )}
      <header className="customer-header">
        <h1>주문 내역</h1>
        <Button variant="ghost" onClick={() => navigate('/customer')} data-testid="history-back-button">
          메뉴로
        </Button>
      </header>

      {loading ? (
        <div className="center-screen">
          <Spinner />
        </div>
      ) : orders.length === 0 ? (
        <p className="muted" style={{ padding: 16 }}>
          아직 주문 내역이 없습니다.
        </p>
      ) : (
        <div className="order-list">
          {orders.map((o) => (
            <div className="card" key={o.id} data-testid={`history-order-${o.order_number}`}>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <strong>#{o.order_number}</strong>
                <StatusBadge status={o.status} />
              </div>
              <div className="muted" style={{ fontSize: 13, margin: '4px 0 8px' }}>
                {formatTime(o.created_at)}
              </div>
              {o.items.map((it, idx) => (
                <div className="order-item-row" key={idx}>
                  <span>
                    {it.menu_name} × {it.quantity}
                  </span>
                  <span>{formatKRW(it.subtotal)}</span>
                </div>
              ))}
              <div className="order-item-row">
                <strong>합계</strong>
                <strong>{formatKRW(o.total_amount)}</strong>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
