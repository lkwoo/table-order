// AuthStore: token persistence in localStorage.
// Admin JWT and table session token are stored separately so both roles can
// coexist in the same browser (e.g. during development).

const ADMIN_TOKEN_KEY = 'to.admin.jwt'
const ADMIN_STORE_KEY = 'to.admin.store_id'
const ADMIN_ID_KEY = 'to.admin.admin_id'

const SESSION_TOKEN_KEY = 'to.table.session_token'
const SESSION_ID_KEY = 'to.table.session_id'
const SESSION_TABLE_KEY = 'to.table.table_id'
const SESSION_STORE_KEY = 'to.table.store_id'

export interface AdminAuth {
  token: string
  storeId: string
  adminId: string
}

export interface TableAuth {
  token: string
  sessionId: string
  tableId: string
  storeId: string
}

export const AuthStore = {
  // ---- Admin ----
  saveAdmin(a: AdminAuth) {
    localStorage.setItem(ADMIN_TOKEN_KEY, a.token)
    localStorage.setItem(ADMIN_STORE_KEY, a.storeId)
    localStorage.setItem(ADMIN_ID_KEY, a.adminId)
  },
  getAdmin(): AdminAuth | null {
    const token = localStorage.getItem(ADMIN_TOKEN_KEY)
    const storeId = localStorage.getItem(ADMIN_STORE_KEY)
    const adminId = localStorage.getItem(ADMIN_ID_KEY)
    if (!token || !storeId || !adminId) return null
    return { token, storeId, adminId }
  },
  clearAdmin() {
    localStorage.removeItem(ADMIN_TOKEN_KEY)
    localStorage.removeItem(ADMIN_STORE_KEY)
    localStorage.removeItem(ADMIN_ID_KEY)
  },

  // ---- Table session ----
  saveTable(t: TableAuth) {
    localStorage.setItem(SESSION_TOKEN_KEY, t.token)
    localStorage.setItem(SESSION_ID_KEY, t.sessionId)
    localStorage.setItem(SESSION_TABLE_KEY, t.tableId)
    localStorage.setItem(SESSION_STORE_KEY, t.storeId)
  },
  getTable(): TableAuth | null {
    const token = localStorage.getItem(SESSION_TOKEN_KEY)
    const sessionId = localStorage.getItem(SESSION_ID_KEY)
    const tableId = localStorage.getItem(SESSION_TABLE_KEY)
    const storeId = localStorage.getItem(SESSION_STORE_KEY)
    if (!token || !sessionId || !tableId || !storeId) return null
    return { token, sessionId, tableId, storeId }
  },
  clearTable() {
    localStorage.removeItem(SESSION_TOKEN_KEY)
    localStorage.removeItem(SESSION_ID_KEY)
    localStorage.removeItem(SESSION_TABLE_KEY)
    localStorage.removeItem(SESSION_STORE_KEY)
  },
}
