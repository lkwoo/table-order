import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiClient, ApiError } from '../shared/api'
import { Button, Spinner, formatKRW } from '../shared/ui'
import { useCart } from './CartContext'
import type { Order } from '../shared/types'

type SubmitState = 'idle' | 'submitting' | 'success' | 'error'

function uuid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

// C10: order submission with idempotency key (stable across retries) + error handling.
export default function OrderSubmitView() {
  const { items, total, clear } = useCart()
  const navigate = useNavigate()
  const [state, setState] = useState<SubmitState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [order, setOrder] = useState<Order | null>(null)
  // Idempotency key is generated once and reused for every retry attempt.
  const idempotencyKey = useRef<string>(uuid())

  const submit = async () => {
    if (items.length === 0) return
    setState('submitting')
    setError(null)
    try {
      const created = await ApiClient.createOrder({
        idempotency_key: idempotencyKey.current,
        items: items.map((i) => ({ menu_id: i.menu_id, quantity: i.quantity })),
      })
      setOrder(created)
      setState('success')
      clear() // clear cart on success
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : '주문 전송에 실패했습니다. 장바구니는 유지됩니다.'
      setError(msg)
      setState('error')
    }
  }

  // Auto-submit on first mount.
  useEffect(() => {
    if (state === 'idle') submit()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (state === 'success' && order) {
    return <OrderSuccess order={order} />
  }

  return (
    <div className="customer-shell">
      <header className="customer-header">
        <h1>주문 전송</h1>
      </header>
      <div className="order-list">
        {state === 'submitting' && (
          <div className="card center-screen" style={{ minHeight: 160 }}>
            <Spinner />
            <p style={{ marginTop: 12 }}>주문을 전송하는 중입니다...</p>
          </div>
        )}
        {state === 'error' && (
          <div className="card">
            <p className="error-text" data-testid="submit-error">
              {error}
            </p>
            <div className="row" style={{ justifyContent: 'space-between', marginTop: 12 }}>
              <Button
                variant="secondary"
                onClick={() => navigate('/customer/confirm')}
                data-testid="submit-back-button"
              >
                장바구니로
              </Button>
              <Button onClick={submit} data-testid="submit-retry-button">
                다시 시도 ({formatKRW(total)})
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// OrderSuccess: shows order number, 5s countdown, then redirect to menu (C10 / 3.1.4).
function OrderSuccess({ order }: { order: Order }) {
  const navigate = useNavigate()
  const [count, setCount] = useState(5)

  useEffect(() => {
    if (count <= 0) {
      navigate('/customer', { replace: true })
      return
    }
    const t = setTimeout(() => setCount((c) => c - 1), 1000)
    return () => clearTimeout(t)
  }, [count, navigate])

  return (
    <div className="success-screen" data-testid="order-success">
      <div>✅ 주문이 접수되었습니다</div>
      <div className="success-number" data-testid="order-success-number">
        #{order.order_number}
      </div>
      <div>{formatKRW(order.total_amount)}</div>
      <p className="muted">{count}초 후 메뉴 화면으로 이동합니다.</p>
      <Button onClick={() => navigate('/customer', { replace: true })} data-testid="order-success-menu-button">
        메뉴로 돌아가기
      </Button>
    </div>
  )
}
