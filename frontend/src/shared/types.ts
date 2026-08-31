// Shared TypeScript types matching the backend REST API contract.

export type OrderStatus = '대기중' | '준비중' | '완료'

export const ORDER_STATUSES: OrderStatus[] = ['대기중', '준비중', '완료']

// Forward-only transitions: 대기중 → {준비중, 완료}, 준비중 → 완료, 완료 → (none)
export const ALLOWED_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  대기중: ['준비중', '완료'],
  준비중: ['완료'],
  완료: [],
}

// ---- Auth ----
export interface AdminLoginResponse {
  access_token: string
  token_type: string
  expires_at: string
  store_id: string
  admin_id: string
}

export interface AdminVerifyResponse {
  admin_id: string
  store_id: string
}

export interface TableLoginResponse {
  session_token: string
  table_id: string
  session_id: string
  expires_at: string
}

export interface TableVerifyResponse {
  table_id: string
  session_id: string
  store_id: string
  expires_at: string
}

// ---- Menu ----
export interface MenuItem {
  id: string
  name: string
  price: number
  description: string | null
  image_url: string | null
}

export interface MenuCategoryGroup {
  category_id: string
  category_name: string
  display_order: number
  menus: MenuItem[]
}

// Admin menu representation (includes is_active + category + order)
export interface AdminMenuItem {
  id: string
  name: string
  price: number
  description: string | null
  image_url: string | null
  category_id: string
  display_order: number
  is_active: boolean
}

export interface AdminMenuCategoryGroup {
  category_id: string
  category_name: string
  display_order: number
  menus: AdminMenuItem[]
}

export interface Category {
  id: string
  name: string
  display_order: number
}

// ---- Orders ----
export interface OrderLineItem {
  menu_name: string
  unit_price: number
  quantity: number
  subtotal: number
}

export interface Order {
  id: string
  order_number: number
  status: OrderStatus
  total_amount: number
  items: OrderLineItem[]
  created_at: string
}

export interface CreateOrderRequest {
  idempotency_key: string
  items: { menu_id: string; quantity: number }[]
}

// ---- Dashboard ----
export interface RecentOrderPreview {
  order_number: number
  status: OrderStatus
  summary: string
}

export interface DashboardCard {
  table_id: string
  table_number: string
  total_amount: number
  recent_orders: RecentOrderPreview[]
  has_new: boolean
}

// ---- Tables ----
export interface TableSummary {
  table_id: string
  table_number: string
}

export interface CreateTableResponse {
  table_id: string
  table_number: string
  session_id: string
}

export interface EndSessionResponse {
  table_id: string
  archived_count: number
}

// ---- History ----
export interface HistoryOrder {
  order_number: number
  ordered_at: string
  completed_at: string | null
  total_amount: number
  items: OrderLineItem[]
}

// ---- Cart (client only) ----
export interface CartLine {
  menu_id: string
  name: string
  price: number
  quantity: number
}

// ---- SSE events ----
export interface SSEEvent<T = unknown> {
  type: string
  data: T
}
