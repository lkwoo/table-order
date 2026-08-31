import React, { createContext, useContext, useEffect, useState } from 'react'
import type { CartLine, MenuItem } from '../shared/types'

const CART_KEY = 'to.cart'

interface CartState {
  items: CartLine[]
  total: number
  add: (menu: MenuItem, qty?: number) => void
  changeQty: (menuId: string, qty: number) => void
  remove: (menuId: string) => void
  clear: () => void
}

const Ctx = createContext<CartState>({
  items: [],
  total: 0,
  add: () => {},
  changeQty: () => {},
  remove: () => {},
  clear: () => {},
})

function loadCart(): CartLine[] {
  try {
    const raw = localStorage.getItem(CART_KEY)
    return raw ? (JSON.parse(raw) as CartLine[]) : []
  } catch {
    return []
  }
}

const clampQty = (q: number) => Math.max(1, Math.min(99, Math.floor(q)))

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartLine[]>(() => loadCart())

  // Sync to localStorage on every change (survives refresh — C6-C8).
  useEffect(() => {
    localStorage.setItem(CART_KEY, JSON.stringify(items))
  }, [items])

  const add = (menu: MenuItem, qty = 1) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.menu_id === menu.id)
      if (existing) {
        return prev.map((i) =>
          i.menu_id === menu.id ? { ...i, quantity: clampQty(i.quantity + qty) } : i,
        )
      }
      return [
        ...prev,
        { menu_id: menu.id, name: menu.name, price: menu.price, quantity: clampQty(qty) },
      ]
    })
  }

  const changeQty = (menuId: string, qty: number) => {
    setItems((prev) => {
      // qty 0 → remove the line (per U7 §3).
      if (qty <= 0) return prev.filter((i) => i.menu_id !== menuId)
      return prev.map((i) => (i.menu_id === menuId ? { ...i, quantity: clampQty(qty) } : i))
    })
  }

  const remove = (menuId: string) => setItems((prev) => prev.filter((i) => i.menu_id !== menuId))
  const clear = () => setItems([])

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0)

  return (
    <Ctx.Provider value={{ items, total, add, changeQty, remove, clear }}>{children}</Ctx.Provider>
  )
}

export function useCart() {
  return useContext(Ctx)
}
