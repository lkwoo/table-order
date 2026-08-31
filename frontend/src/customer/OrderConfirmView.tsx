import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, formatKRW } from '../shared/ui'
import { useCart } from './CartContext'

// C9: final order review before confirming.
export default function OrderConfirmView() {
  const { items, total } = useCart()
  const navigate = useNavigate()

  // If cart emptied, go back to menu.
  useEffect(() => {
    if (items.length === 0) navigate('/customer', { replace: true })
  }, [items.length, navigate])

  return (
    <div className="customer-shell">
      <header className="customer-header">
        <h1>주문 확인</h1>
      </header>
      <div className="order-list">
        <div className="card">
          {items.map((line) => (
            <div className="order-item-row" key={line.menu_id}>
              <span>
                {line.name} × {line.quantity}
              </span>
              <span>{formatKRW(line.price * line.quantity)}</span>
            </div>
          ))}
          <hr />
          <div className="order-item-row">
            <strong>총 금액</strong>
            <strong data-testid="confirm-total">{formatKRW(total)}</strong>
          </div>
        </div>
        <p className="muted">최종 금액은 서버에서 다시 계산되어 확정됩니다.</p>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <Button variant="secondary" onClick={() => navigate('/customer')} data-testid="confirm-back-button">
            돌아가기
          </Button>
          <Button onClick={() => navigate('/customer/submit')} data-testid="confirm-submit-button">
            주문 확정
          </Button>
        </div>
      </div>
    </div>
  )
}
