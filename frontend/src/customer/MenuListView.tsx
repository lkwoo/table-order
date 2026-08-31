import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiClient } from '../shared/api'
import type { MenuCategoryGroup, MenuItem } from '../shared/types'
import { Button, Spinner, formatKRW, useToast } from '../shared/ui'
import { useCart } from './CartContext'
import { useCustomerAuth } from './CustomerAuthContext'
import MenuDetailModal from './MenuDetailModal'
import CartDrawer from './CartDrawer'

// C3: menu list grouped by category with tab navigation.
export default function MenuListView() {
  const { logout } = useCustomerAuth()
  const { items, total } = useCart()
  const toast = useToast()
  const navigate = useNavigate()
  const [groups, setGroups] = useState<MenuCategoryGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [detail, setDetail] = useState<MenuItem | null>(null)
  const [cartOpen, setCartOpen] = useState(false)

  useEffect(() => {
    ApiClient.getMenus()
      .then((g) => {
        setGroups(g)
        if (g.length) setActiveCategory(g[0].category_id)
      })
      .catch(() => toast.show('메뉴를 불러오지 못했습니다.', 'error'))
      .finally(() => setLoading(false))
  }, [toast])

  const active = useMemo(
    () => groups.find((g) => g.category_id === activeCategory) ?? null,
    [groups, activeCategory],
  )

  const cartCount = items.reduce((n, i) => n + i.quantity, 0)

  if (loading) {
    return (
      <div className="center-screen">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="customer-shell">
      <header className="customer-header">
        <h1>메뉴</h1>
        <div className="row">
          <Button variant="ghost" onClick={() => navigate('/customer/history')} data-testid="nav-history-button">
            주문 내역
          </Button>
          <Button variant="ghost" onClick={logout} data-testid="customer-logout-button">
            로그아웃
          </Button>
        </div>
      </header>

      <div className="category-tabs">
        {groups.map((g) => (
          <button
            key={g.category_id}
            className={`category-tab ${g.category_id === activeCategory ? 'active' : ''}`}
            onClick={() => setActiveCategory(g.category_id)}
            data-testid={`category-tab-${g.category_id}`}
          >
            {g.category_name}
          </button>
        ))}
      </div>

      {active && active.menus.length === 0 && (
        <p className="muted" style={{ padding: 16 }}>
          이 카테고리에 메뉴가 없습니다.
        </p>
      )}

      <div className="menu-grid">
        {active?.menus.map((m) => (
          <div
            key={m.id}
            className="card menu-card"
            onClick={() => setDetail(m)}
            data-testid={`menu-card-${m.id}`}
          >
            {m.image_url ? (
              <img className="menu-card__img" src={m.image_url} alt={m.name} loading="lazy" />
            ) : (
              <div className="menu-card__img">🍽️</div>
            )}
            <div className="menu-card__body">
              <div className="menu-card__name">{m.name}</div>
              <div className="menu-card__price">{formatKRW(m.price)}</div>
            </div>
          </div>
        ))}
      </div>

      {cartCount > 0 && (
        <Button className="cart-fab" onClick={() => setCartOpen(true)} data-testid="open-cart-button">
          장바구니 {cartCount}개 · {formatKRW(total)}
        </Button>
      )}

      <MenuDetailModal menu={detail} onClose={() => setDetail(null)} />
      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} />
    </div>
  )
}
