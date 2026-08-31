import { useCallback, useEffect, useState } from 'react'
import { ApiClient, ApiError } from '../shared/api'
import type { AdminMenuCategoryGroup, AdminMenuItem, Category } from '../shared/types'
import { Button, Modal, Spinner, formatKRW, useToast } from '../shared/ui'

// A9-A13: menu management (list, create, edit, soft-delete, reorder).
export default function MenuManagementView() {
  const toast = useToast()
  const [groups, setGroups] = useState<AdminMenuCategoryGroup[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<AdminMenuItem | null>(null)
  const [creating, setCreating] = useState(false)

  const load = useCallback(() => {
    Promise.all([ApiClient.getAdminMenus(), ApiClient.getCategories()])
      .then(([g, c]) => {
        setGroups(g)
        setCategories(c)
      })
      .catch(() => toast.show('메뉴를 불러오지 못했습니다.', 'error'))
      .finally(() => setLoading(false))
  }, [toast])

  useEffect(() => {
    load()
  }, [load])

  const softDelete = async (m: AdminMenuItem) => {
    if (!confirm(`"${m.name}" 메뉴를 삭제하시겠습니까? (고객 화면에서 숨겨집니다)`)) return
    try {
      await ApiClient.deleteMenu(m.id)
      toast.show('삭제되었습니다.', 'success')
      load()
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : '삭제 실패', 'error')
    }
  }

  const reorder = async (group: AdminMenuCategoryGroup, index: number, dir: -1 | 1) => {
    const ids = group.menus.map((m) => m.id)
    const target = index + dir
    if (target < 0 || target >= ids.length) return
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    try {
      await ApiClient.reorderMenus(group.category_id, ids)
      load()
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : '순서 변경 실패', 'error')
    }
  }

  if (loading) return <Spinner />

  return (
    <div>
      <div className="section-title">
        <h2 style={{ margin: 0 }}>메뉴 관리</h2>
        <Button onClick={() => setCreating(true)} data-testid="open-menu-create-button">
          + 메뉴 등록
        </Button>
      </div>

      {groups.map((g) => (
        <div className="card" key={g.category_id} style={{ marginBottom: 16 }}>
          <h3 style={{ marginTop: 0 }}>{g.category_name}</h3>
          <table className="menu-mgmt-table">
            <thead>
              <tr>
                <th style={{ width: 90 }}>순서</th>
                <th>메뉴</th>
                <th>가격</th>
                <th style={{ width: 160 }}>액션</th>
              </tr>
            </thead>
            <tbody>
              {g.menus.map((m, idx) => (
                <tr key={m.id} className={m.is_active ? '' : 'inactive'} data-testid={`menu-row-${m.id}`}>
                  <td>
                    <span className="reorder-btns">
                      <button
                        onClick={() => reorder(g, idx, -1)}
                        disabled={idx === 0}
                        data-testid={`menu-up-${m.id}`}
                        aria-label="위로"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => reorder(g, idx, 1)}
                        disabled={idx === g.menus.length - 1}
                        data-testid={`menu-down-${m.id}`}
                        aria-label="아래로"
                      >
                        ↓
                      </button>
                    </span>
                  </td>
                  <td>
                    {m.name}
                    {!m.is_active && <span className="muted"> (삭제됨)</span>}
                    {m.description && <div className="muted" style={{ fontSize: 12 }}>{m.description}</div>}
                  </td>
                  <td>{formatKRW(m.price)}</td>
                  <td>
                    <Button variant="secondary" onClick={() => setEditing(m)} data-testid={`menu-edit-${m.id}`}>
                      수정
                    </Button>{' '}
                    {m.is_active && (
                      <Button variant="ghost" onClick={() => softDelete(m)} data-testid={`menu-delete-${m.id}`}>
                        삭제
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
              {g.menus.length === 0 && (
                <tr>
                  <td colSpan={4} className="muted">
                    메뉴가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ))}

      {(creating || editing) && (
        <MenuForm
          menu={editing}
          categories={categories}
          onClose={() => {
            setCreating(false)
            setEditing(null)
          }}
          onSaved={() => {
            setCreating(false)
            setEditing(null)
            load()
          }}
        />
      )}
    </div>
  )
}

// MenuForm: create/edit with client-side validation (A10/A11).
function MenuForm({
  menu,
  categories,
  onClose,
  onSaved,
}: {
  menu: AdminMenuItem | null
  categories: Category[]
  onClose: () => void
  onSaved: () => void
}) {
  const toast = useToast()
  const [name, setName] = useState(menu?.name ?? '')
  const [price, setPrice] = useState(menu ? String(menu.price) : '')
  const [categoryId, setCategoryId] = useState(menu?.category_id ?? categories[0]?.id ?? '')
  const [description, setDescription] = useState(menu?.description ?? '')
  const [imageUrl, setImageUrl] = useState(menu?.image_url ?? '')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)

  const validate = (): boolean => {
    const e: Record<string, string> = {}
    if (!name.trim()) e.name = '메뉴명을 입력해주세요.'
    const p = Number(price)
    if (!price || !Number.isInteger(p)) e.price = '가격은 정수여야 합니다.'
    else if (p < 1000 || p > 100000) e.price = '가격은 1,000 ~ 100,000원 사이여야 합니다.'
    if (!categoryId) e.category = '카테고리를 선택해주세요.'
    if (imageUrl && !/^https?:\/\/.+/.test(imageUrl)) e.image = '올바른 URL 형식이 아닙니다.'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const submit = async () => {
    if (!validate()) return
    setBusy(true)
    const payload = {
      name: name.trim(),
      price: Number(price),
      category_id: categoryId,
      description: description.trim() || undefined,
      image_url: imageUrl.trim() || undefined,
    }
    try {
      if (menu) await ApiClient.updateMenu(menu.id, payload)
      else await ApiClient.createMenu(payload)
      toast.show(menu ? '수정되었습니다.' : '등록되었습니다.', 'success')
      onSaved()
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : '저장 실패', 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open title={menu ? '메뉴 수정' : '메뉴 등록'} onClose={onClose} testId="menu-form-modal">
      <div className="field">
        <label>메뉴명 *</label>
        <input value={name} onChange={(e) => setName(e.target.value)} data-testid="menu-form-name-input" />
        {errors.name && <div className="error-text">{errors.name}</div>}
      </div>
      <div className="field">
        <label>가격 (원) *</label>
        <input
          type="number"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          data-testid="menu-form-price-input"
        />
        {errors.price && <div className="error-text">{errors.price}</div>}
      </div>
      <div className="field">
        <label>카테고리 *</label>
        <select
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          data-testid="menu-form-category-select"
        >
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {errors.category && <div className="error-text">{errors.category}</div>}
      </div>
      <div className="field">
        <label>설명</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          data-testid="menu-form-description-input"
        />
      </div>
      <div className="field">
        <label>이미지 URL</label>
        <input
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          data-testid="menu-form-image-input"
          placeholder="https://..."
        />
        {errors.image && <div className="error-text">{errors.image}</div>}
      </div>
      <div className="row" style={{ justifyContent: 'flex-end' }}>
        <Button variant="secondary" onClick={onClose} data-testid="menu-form-cancel-button">
          취소
        </Button>
        <Button onClick={submit} disabled={busy} data-testid="menu-form-submit-button">
          저장
        </Button>
      </div>
    </Modal>
  )
}
