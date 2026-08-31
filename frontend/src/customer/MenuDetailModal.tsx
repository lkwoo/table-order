import { Button, Modal, formatKRW } from '../shared/ui'
import type { MenuItem } from '../shared/types'
import { useCart } from './CartContext'

// C4: menu detail. Uses list data (name, price, description, image).
export default function MenuDetailModal({
  menu,
  onClose,
}: {
  menu: MenuItem | null
  onClose: () => void
}) {
  const { add } = useCart()
  if (!menu) return null

  return (
    <Modal open={!!menu} title={menu.name} onClose={onClose} testId="menu-detail-modal">
      {menu.image_url ? (
        <img
          src={menu.image_url}
          alt={menu.name}
          style={{ width: '100%', maxHeight: 220, objectFit: 'cover', borderRadius: 10 }}
          loading="lazy"
        />
      ) : (
        <div className="menu-card__img" style={{ height: 160, borderRadius: 10 }}>🍽️</div>
      )}
      <p style={{ color: 'var(--color-muted)' }}>{menu.description || '설명이 없습니다.'}</p>
      <div className="row" style={{ justifyContent: 'space-between', marginTop: 12 }}>
        <strong style={{ fontSize: 20, color: 'var(--color-primary)' }}>
          {formatKRW(menu.price)}
        </strong>
        <div className="row">
          <Button variant="secondary" onClick={onClose} data-testid="menu-detail-close-button">
            닫기
          </Button>
          <Button
            onClick={() => {
              add(menu, 1)
              onClose()
            }}
            data-testid="menu-detail-add-button"
          >
            장바구니 담기
          </Button>
        </div>
      </div>
    </Modal>
  )
}
