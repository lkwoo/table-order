import { useState } from 'react'
import { AdminAuthProvider, useAdminAuth } from './AdminAuthContext'
import { Button, Spinner } from '../shared/ui'
import AdminLoginView from './AdminLoginView'
import DashboardView from './DashboardView'
import MenuManagementView from './MenuManagementView'
import './admin.css'

type Tab = 'dashboard' | 'menus'

function AdminShell() {
  const { auth, ready, logout } = useAdminAuth()
  const [tab, setTab] = useState<Tab>('dashboard')

  if (!ready) {
    return (
      <div className="center-screen">
        <Spinner />
      </div>
    )
  }
  if (!auth) return <AdminLoginView />

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <h1>테이블오더 관리자</h1>
        <div className="admin-nav">
          <button
            className={tab === 'dashboard' ? 'active' : ''}
            onClick={() => setTab('dashboard')}
            data-testid="nav-dashboard-button"
          >
            대시보드
          </button>
          <button
            className={tab === 'menus' ? 'active' : ''}
            onClick={() => setTab('menus')}
            data-testid="nav-menus-button"
          >
            메뉴 관리
          </button>
          <Button variant="danger" onClick={logout} data-testid="admin-logout-button">
            로그아웃
          </Button>
        </div>
      </header>
      <div className="admin-body">{tab === 'dashboard' ? <DashboardView /> : <MenuManagementView />}</div>
    </div>
  )
}

export default function AdminApp() {
  return (
    <AdminAuthProvider>
      <AdminShell />
    </AdminAuthProvider>
  )
}
