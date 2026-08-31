import { useState } from 'react'
import { useCustomerAuth } from './CustomerAuthContext'
import { Button, Spinner, useToast } from '../shared/ui'
import { ApiError } from '../shared/api'

// C2: table initial login. store_id + table number + password.
export default function TableLoginView() {
  const { login } = useCustomerAuth()
  const toast = useToast()
  const [storeId, setStoreId] = useState('')
  const [tableNumber, setTableNumber] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!storeId.trim() || !tableNumber.trim() || !password) {
      setError('매장 ID, 테이블 번호, 비밀번호를 모두 입력해주세요.')
      return
    }
    setBusy(true)
    try {
      await login(storeId.trim(), tableNumber.trim(), password)
      toast.show('로그인되었습니다.', 'success')
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : '로그인에 실패했습니다.'
      setError(msg)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="center-screen">
      <form className="card" style={{ width: 360 }} onSubmit={submit} data-testid="table-login-form">
        <h2 style={{ marginTop: 0 }}>테이블 로그인</h2>
        <div className="field">
          <label>매장 ID</label>
          <input
            value={storeId}
            onChange={(e) => setStoreId(e.target.value)}
            data-testid="table-login-store-input"
            placeholder="매장 ID"
          />
        </div>
        <div className="field">
          <label>테이블 번호</label>
          <input
            value={tableNumber}
            onChange={(e) => setTableNumber(e.target.value)}
            data-testid="table-login-number-input"
            placeholder="예: 5"
          />
        </div>
        <div className="field">
          <label>비밀번호</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            data-testid="table-login-password-input"
          />
        </div>
        {error && <div className="error-text" data-testid="table-login-error">{error}</div>}
        <Button type="submit" block disabled={busy} data-testid="table-login-submit-button">
          {busy ? <Spinner /> : '로그인'}
        </Button>
      </form>
    </div>
  )
}
