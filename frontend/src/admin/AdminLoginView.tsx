import { useState } from 'react'
import { useAdminAuth } from './AdminAuthContext'
import { Button, Spinner, useToast } from '../shared/ui'
import { ApiError } from '../shared/api'

// A1: admin login with store_id + username + password.
export default function AdminLoginView() {
  const { login } = useAdminAuth()
  const toast = useToast()
  const [storeId, setStoreId] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!storeId.trim() || !username.trim() || !password) {
      setError('매장 ID, 사용자명, 비밀번호를 모두 입력해주세요.')
      return
    }
    setBusy(true)
    try {
      await login(storeId.trim(), username.trim(), password)
      toast.show('로그인되었습니다.', 'success')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '로그인에 실패했습니다.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="center-screen">
      <form className="card" style={{ width: 360 }} onSubmit={submit} data-testid="admin-login-form">
        <h2 style={{ marginTop: 0 }}>관리자 로그인</h2>
        <div className="field">
          <label>매장 ID</label>
          <input
            value={storeId}
            onChange={(e) => setStoreId(e.target.value)}
            data-testid="admin-login-store-input"
          />
        </div>
        <div className="field">
          <label>사용자명</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            data-testid="admin-login-username-input"
          />
        </div>
        <div className="field">
          <label>비밀번호</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            data-testid="admin-login-password-input"
          />
        </div>
        {error && (
          <div className="error-text" data-testid="admin-login-error">
            {error}
          </div>
        )}
        <Button type="submit" block disabled={busy} data-testid="admin-login-submit-button">
          {busy ? <Spinner /> : '로그인'}
        </Button>
      </form>
    </div>
  )
}
