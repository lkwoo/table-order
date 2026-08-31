import React, { createContext, useContext, useEffect, useState } from 'react'
import { ApiClient } from '../shared/api'
import { AuthStore, type AdminAuth } from '../shared/auth'

interface AdminAuthState {
  auth: AdminAuth | null
  ready: boolean
  login: (storeId: string, username: string, password: string) => Promise<void>
  logout: () => void
}

const Ctx = createContext<AdminAuthState>({
  auth: null,
  ready: false,
  login: async () => {},
  logout: () => {},
})

export function AdminAuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AdminAuth | null>(null)
  const [ready, setReady] = useState(false)

  // A1: keep session across refresh — verify stored JWT.
  useEffect(() => {
    let cancelled = false
    const stored = AuthStore.getAdmin()
    if (!stored) {
      setReady(true)
      return
    }
    ApiClient.adminVerify()
      .then((v) => {
        if (cancelled) return
        const merged: AdminAuth = { token: stored.token, storeId: v.store_id, adminId: v.admin_id }
        AuthStore.saveAdmin(merged)
        setAuth(merged)
      })
      .catch(() => {
        AuthStore.clearAdmin()
        setAuth(null)
      })
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = async (storeId: string, username: string, password: string) => {
    const res = await ApiClient.adminLogin(storeId, username, password)
    const next: AdminAuth = { token: res.access_token, storeId: res.store_id, adminId: res.admin_id }
    AuthStore.saveAdmin(next)
    setAuth(next)
  }

  const logout = () => {
    AuthStore.clearAdmin()
    setAuth(null)
  }

  return <Ctx.Provider value={{ auth, ready, login, logout }}>{children}</Ctx.Provider>
}

export function useAdminAuth() {
  return useContext(Ctx)
}
