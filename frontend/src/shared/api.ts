// ApiClient: fetch wrapper with auth-header injection and network auto-retry.
// - Admin endpoints: Authorization: Bearer <jwt>
// - Customer endpoints: X-Session-Token: <session_token>
// - Order creation: adds Idempotency-Key header (and idempotency_key in body)
// - Auto-retry: up to 3 attempts, 3s interval, on network error or 5xx.

import { AuthStore } from './auth'
import type {
  AdminLoginResponse,
  AdminMenuCategoryGroup,
  AdminMenuItem,
  AdminVerifyResponse,
  Category,
  CreateOrderRequest,
  CreateTableResponse,
  DashboardCard,
  EndSessionResponse,
  HistoryOrder,
  MenuCategoryGroup,
  MenuItem,
  Order,
  OrderStatus,
  TableLoginResponse,
  TableSummary,
  TableVerifyResponse,
} from './types'

const BASE = '/api'
const MAX_RETRIES = 3
const RETRY_INTERVAL_MS = 3000

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

type Auth = 'admin' | 'session' | 'none'

interface RequestOptions {
  method?: string
  auth?: Auth
  body?: unknown
  query?: Record<string, string | undefined>
  idempotencyKey?: string
  retry?: boolean
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

function buildUrl(path: string, query?: Record<string, string | undefined>): string {
  const url = new URL(BASE + path, window.location.origin)
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    }
  }
  return url.pathname + url.search
}

function authHeaders(auth: Auth): Record<string, string> {
  if (auth === 'admin') {
    const a = AuthStore.getAdmin()
    return a ? { Authorization: `Bearer ${a.token}` } : {}
  }
  if (auth === 'session') {
    const t = AuthStore.getTable()
    return t ? { 'X-Session-Token': t.token } : {}
  }
  return {}
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', auth = 'none', body, query, idempotencyKey, retry = true } = opts
  const url = buildUrl(path, query)
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...authHeaders(auth),
  }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey

  const maxAttempts = retry ? MAX_RETRIES : 1
  let lastErr: unknown

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res = await fetch(url, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
      })

      // Retry on server errors (5xx).
      if (res.status >= 500 && attempt < maxAttempts) {
        await sleep(RETRY_INTERVAL_MS)
        continue
      }

      if (!res.ok) {
        let detail: unknown = undefined
        let message = `요청 실패 (${res.status})`
        try {
          const data = await res.json()
          detail = data
          if (data?.detail) {
            message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
          }
        } catch {
          /* ignore parse errors */
        }
        throw new ApiError(res.status, message, detail)
      }

      if (res.status === 204) return undefined as T
      const text = await res.text()
      return (text ? JSON.parse(text) : undefined) as T
    } catch (err) {
      lastErr = err
      // ApiError from a non-5xx response should not be retried.
      if (err instanceof ApiError) throw err
      // Network error → retry.
      if (attempt < maxAttempts) {
        await sleep(RETRY_INTERVAL_MS)
        continue
      }
    }
  }
  throw lastErr instanceof Error
    ? lastErr
    : new ApiError(0, '네트워크 오류: 서버에 연결할 수 없습니다.')
}

export const ApiClient = {
  // ---- Auth (U1) ----
  adminLogin(store_id: string, username: string, password: string) {
    return request<AdminLoginResponse>('/auth/admin-login', {
      method: 'POST',
      body: { store_id, username, password },
    })
  },
  adminVerify() {
    return request<AdminVerifyResponse>('/auth/admin-verify', { auth: 'admin', retry: false })
  },
  tableLogin(store_id: string, table_number: string, password: string) {
    return request<TableLoginResponse>('/auth/table-login', {
      method: 'POST',
      body: { store_id, table_number, password },
    })
  },
  tableVerify() {
    return request<TableVerifyResponse>('/auth/table-verify', { auth: 'session', retry: false })
  },

  // ---- Customer menu (U2) ----
  getMenus() {
    return request<MenuCategoryGroup[]>('/menus', { auth: 'session' })
  },
  getMenu(menuId: string) {
    return request<MenuItem>(`/menus/${menuId}`, { auth: 'session' })
  },

  // ---- Customer orders (U3) ----
  createOrder(req: CreateOrderRequest) {
    return request<Order>('/orders', {
      method: 'POST',
      auth: 'session',
      body: req,
      idempotencyKey: req.idempotency_key,
    })
  },
  getOrders() {
    return request<Order[]>('/orders', { auth: 'session' })
  },

  // ---- Admin dashboard / orders (U4) ----
  getDashboard() {
    return request<DashboardCard[]>('/admin/dashboard', { auth: 'admin' })
  },
  getTableOrders(tableId: string) {
    return request<Order[]>(`/admin/tables/${tableId}/orders`, { auth: 'admin' })
  },
  updateOrderStatus(orderId: string, status: OrderStatus) {
    return request<Order>(`/admin/orders/${orderId}/status`, {
      method: 'PATCH',
      auth: 'admin',
      body: { status },
      retry: false,
    })
  },
  deleteOrder(orderId: string) {
    return request<{ table_id: string; table_total: number }>(`/admin/orders/${orderId}`, {
      method: 'DELETE',
      auth: 'admin',
      retry: false,
    })
  },

  // ---- Admin tables / sessions (U5) ----
  createTable(table_number: string, password: string) {
    return request<CreateTableResponse>('/admin/tables', {
      method: 'POST',
      auth: 'admin',
      body: { table_number, password },
      retry: false,
    })
  },
  getTables() {
    return request<TableSummary[]>('/admin/tables', { auth: 'admin' })
  },
  endSession(tableId: string) {
    return request<EndSessionResponse>(`/admin/tables/${tableId}/end-session`, {
      method: 'POST',
      auth: 'admin',
      retry: false,
    })
  },
  getHistory(tableId: string, filter: string, from?: string, to?: string) {
    return request<HistoryOrder[]>(`/admin/tables/${tableId}/history`, {
      auth: 'admin',
      query: { filter, from, to },
    })
  },

  // ---- Admin menu management (U6) ----
  getAdminMenus() {
    return request<AdminMenuCategoryGroup[]>('/admin/menus', { auth: 'admin' })
  },
  getCategories() {
    return request<Category[]>('/admin/categories', { auth: 'admin' })
  },
  createMenu(payload: {
    name: string
    price: number
    category_id: string
    description?: string
    image_url?: string
  }) {
    return request<AdminMenuItem>('/admin/menus', {
      method: 'POST',
      auth: 'admin',
      body: payload,
      retry: false,
    })
  },
  updateMenu(
    menuId: string,
    payload: {
      name: string
      price: number
      category_id: string
      description?: string
      image_url?: string
    },
  ) {
    return request<AdminMenuItem>(`/admin/menus/${menuId}`, {
      method: 'PUT',
      auth: 'admin',
      body: payload,
      retry: false,
    })
  },
  deleteMenu(menuId: string) {
    return request<{ id: string; is_active: boolean }>(`/admin/menus/${menuId}`, {
      method: 'DELETE',
      auth: 'admin',
      retry: false,
    })
  },
  reorderMenus(category_id: string, ordered_menu_ids: string[]) {
    return request<{ updated: number }>('/admin/menus/reorder', {
      method: 'PATCH',
      auth: 'admin',
      body: { category_id, ordered_menu_ids },
      retry: false,
    })
  },
}
