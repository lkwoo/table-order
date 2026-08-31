import { useState } from 'react'
import { ApiClient, ApiError } from '../shared/api'
import { Button, Modal, useToast } from '../shared/ui'

// A5: table initial setup — number + password (4-10 chars) → creates table + session.
export default function TableSetupModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean
  onClose: () => void
  onCreated: () => void
}) {
  const toast = useToast()
  const [tableNumber, setTableNumber] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const reset = () => {
    setTableNumber('')
    setPassword('')
    setError(null)
  }

  const submit = async () => {
    setError(null)
    if (!tableNumber.trim()) {
      setError('테이블 번호를 입력해주세요.')
      return
    }
    if (password.length < 4 || password.length > 10) {
      setError('비밀번호는 4~10자리여야 합니다.')
      return
    }
    setBusy(true)
    try {
      await ApiClient.createTable(tableNumber.trim(), password)
      toast.show('테이블이 생성되었습니다.', 'success')
      reset()
      onCreated()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '테이블 생성에 실패했습니다.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} title="테이블 설정" onClose={onClose} testId="table-setup-modal">
      <div className="field">
        <label>테이블 번호</label>
        <input
          value={tableNumber}
          onChange={(e) => setTableNumber(e.target.value)}
          data-testid="table-setup-number-input"
        />
      </div>
      <div className="field">
        <label>비밀번호 (4~10자리)</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          data-testid="table-setup-password-input"
        />
      </div>
      {error && (
        <div className="error-text" data-testid="table-setup-error">
          {error}
        </div>
      )}
      <div className="row" style={{ justifyContent: 'flex-end', marginTop: 12 }}>
        <Button variant="secondary" onClick={onClose} data-testid="table-setup-cancel-button">
          취소
        </Button>
        <Button onClick={submit} disabled={busy} data-testid="table-setup-submit-button">
          생성
        </Button>
      </div>
    </Modal>
  )
}
