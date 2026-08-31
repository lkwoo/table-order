import React, { createContext, useContext, useEffect, useState } from 'react'
import { ApiClient } from '../shared/api'
import { AuthStore, type TableAuth } from '../shared/auth'

interface CustomerAuthState {
  auth: TableAuth | null
  ready: boolean // bootstrap finished
  login: (storeId: string, tableNumber: string, password: string) => Promise<void>
  logout: () => void
}

const Ctx = createContext<CustomerAuthState>({
  auth: null,
  ready: false,
  login: async () => {},
  logout: () => {},
})

export function CustomerAuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<TableAuth | null>(null)
  const [ready, setReady] = useState(false)

  // Bootstrap auto-login (C1): verify stored session token.
  useEffect(() => {
    let cancelled = false
    const stored = AuthStore.getTable()
    if (!stored) {
      setReady(true)
      return
    }
    ApiClient.tableVerify()
      .then((v) => {
        if (cancelled) return
        const merged: TableAuth = {
          token: stored.token,
          sessionId: v.session_id,
          tableId: v.table_id,
          storeId: v.store_id,
        }
        AuthStore.saveTable(merged)
        setAuth(merged)
      })
      .catch(() => {
        AuthStore.clearTable()
        setAuth(null)
      })
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = async (storeId: string, tableNumber: string, password: string) => {
    const res = await ApiClient.tableLogin(storeId, tableNumber, password)
    const next: TableAuth = {
      token: res.session_token,
      sessionId: res.session_id,
      tableId: res.table_id,
      storeId,
    }
    AuthStore.saveTable(next)
    setAuth(next)
  }

  const logout = () => {
    AuthStore.clearTable()
    setAuth(null)
  }

  return <Ctx.Provider value={{ auth, ready, login, logout }}>{children}</Ctx.Provider>
}

export function useCustomerAuth() {
  return useContext(Ctx)
}
