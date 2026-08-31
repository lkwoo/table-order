import { useNavigate } from 'react-router-dom'
import { Button, Modal, formatKRW } from '../shared/ui'
import { useCart } from './CartContext'

// Cart drawer (C6-C8): quantity control, remove, clear, proceed to confirm.
export default function CartDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { items, total, changeQty, remove, clear } = useCart()
  const navigate = useNavigate()

  return (
    <Modal open={open} title="장바구니" onClose={onClose} testId="cart-drawer">
      {items.length === 0 ? (
        <p className="muted">장바구니가 비어 있습니다.</p>
      ) : (
        <>
          <div className="cart-drawer-lines">
            {items.map((line) => (
              <div className="cart-line" key={line.menu_id} data-testid={`cart-line-${line.menu_id}`}>
                <div>
                  <div style={{ fontWeight: 600 }}>{line.name}</div>
                  <div className="muted">{formatKRW(line.price)}</div>
                </div>
                <div className="qty-control">
                  <button
                    onClick={() => changeQty(line.menu_id, line.quantity - 1)}
                    data-testid={`cart-qty-dec-${line.menu_id}`}
                    aria-label="수량 감소"
                  >
                    −
                  </button>
                  <span data-testid={`cart-qty-${line.menu_id}`}>{line.quantity}</span>
                  <button
                    onClick={() => changeQty(line.menu_id, line.quantity + 1)}
                    data-testid={`cart-qty-inc-${line.menu_id}`}
                    aria-label="수량 증가"
                  >
                    +
                  </button>
                  <Button
                    variant="ghost"
                    onClick={() => remove(line.menu_id)}
                    data-testid={`cart-remove-${line.menu_id}`}
                  >
                    삭제
                  </Button>
                </div>
              </div>
            ))}
          </div>
          <div className="row" style={{ justifyContent: 'space-between', margin: '16px 0' }}>
            <span>총 금액</span>
            <strong style={{ fontSize: 20 }} data-testid="cart-total">
              {formatKRW(total)}
            </strong>
          </div>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <Button variant="ghost" onClick={clear} data-testid="cart-clear-button">
              비우기
            </Button>
            <Button
              onClick={() => {
                onClose()
                navigate('/customer/confirm')
              }}
              data-testid="cart-checkout-button"
            >
              주문하기
            </Button>
          </div>
        </>
      )}
    </Modal>
  )
}
