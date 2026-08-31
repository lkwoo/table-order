# Frontend Components - U7 Frontend

**작성일**: 2026-08-31 | **Unit**: U7 | **스토리**: 전 스토리 UI
**상태관리**: Context + hooks (경량), 장바구니는 localStorage 동기화 (Q8)

---

## 1. 컴포넌트 계층

```
App (Router)
├── /customer  → CustomerApp (CustomerAuthProvider, CartProvider)
│   ├── TableLoginView
│   ├── MenuListView ── MenuDetailModal
│   ├── CartDrawer (CartItem[])
│   ├── OrderConfirmView
│   ├── OrderSubmitView (OrderSuccess)
│   └── OrderHistoryView (uses CustomerSSE)
└── /admin → AdminApp (AdminAuthProvider)
    ├── AdminLoginView
    ├── DashboardView (uses AdminSSE)
    │   └── TableCard[]
    ├── TableOrderDetailPanel (OrderStatusControl, OrderDeleteControl)
    ├── TableSetupModal
    ├── SessionEndControl
    ├── OrderHistoryModal (DateFilter)
    └── MenuManagementView (MenuForm, MenuList, ReorderControl)

shared: ApiClient, AuthStore, SSEClientBase, UIKit(Button/Modal/Badge/Toast)
```

---

## 2. 컴포넌트별 Props/State/상호작용/API

### 고객 (Customer)

| 컴포넌트 | State/Props | 상호작용 | API |
|---------|-------------|----------|-----|
| **CustomerApp** | authState(session) | 부트스트랩 자동 로그인(C1) | `verify` 세션 |
| **TableLoginView** | {tableNumber, password}, error | 제출→로그인 | `POST /auth/table-login` (C2) |
| **MenuListView** | menusByCategory, activeCategory | 카테고리 탭, 메뉴 클릭 | `GET /menus` (C3) |
| **MenuDetailModal** | menu, isOpen | 추가/닫기 | (상세는 목록 데이터 재사용 또는 `GET /menus/{id}`) (C4) |
| **CartProvider(context)** | items[], total | add/changeQty/remove/clear | localStorage 동기화 (C6-C8) |
| **CartDrawer** | items, total | 수량±, 제거, 주문하기 | - |
| **OrderConfirmView** | items, total | 확정/돌아가기 (C9) | - |
| **OrderSubmitView** | status(idle/submitting/success/error), idempotencyKey | 확정 클릭, 재시도 | `POST /orders` (C10) |
| **OrderSuccess** | orderNumber, countdown(5s) | 5초 후 메뉴로 이동 | - |
| **OrderHistoryView** | orders[], connectionState | SSE 상태 반영 | `GET /orders` + `/sse/orders` (C11,C12) |

### 관리자 (Admin)

| 컴포넌트 | State/Props | 상호작용 | API |
|---------|-------------|----------|-----|
| **AdminApp** | authState(jwt) | 자동 로그인/새로고침 유지 | JWT 검증 (A1) |
| **AdminLoginView** | {storeId, username, password}, error | 로그인 | `POST /auth/admin-login` (A1) |
| **DashboardView** | tableCards[], sseState, offline | SSE 구독, 카드 클릭 | `GET /admin/dashboard` + `/sse/dashboard` (A2) |
| **TableCard** | {tableNumber, total, recentOrders, hasNew} | 클릭→상세 | - |
| **TableOrderDetailPanel** | tableId, orders[] | 상태 변경, 삭제 | `GET /admin/tables/{id}/orders` (A3) |
| **OrderStatusControl** | order, allowedNext[] | 상태 선택 | `PATCH /admin/orders/{id}/status` (A4) |
| **OrderDeleteControl** | order, confirmOpen | 삭제 확인 | `DELETE /admin/orders/{id}` (A6) |
| **TableSetupModal** | {tableNumber, password}, error | 생성 | `POST /admin/tables` (A5) |
| **SessionEndControl** | tableId, confirmOpen | 종료 확인 | `POST /admin/tables/{id}/end-session` (A7) |
| **OrderHistoryModal** | history[], dateFilter | 필터 적용/닫기 | `GET /admin/tables/{id}/history` (A8) |
| **MenuManagementView** | menus[], editing | CRUD, 순서 조정 | `GET/POST/PUT/DELETE /admin/menus`, `PATCH /admin/menus/reorder` (A9-A13) |
| **MenuForm** | fields, validationErrors | 저장/취소 | 등록/수정 |
| **ReorderControl** | orderedIds | 드래그앤드롭 | reorder |

### 공용 (Shared)

| 컴포넌트 | 책임 |
|---------|------|
| **ApiClient** | fetch 래퍼, 인증 헤더 주입, 네트워크 오류 자동 재시도 ×3(3초 간격), 주문 생성은 idempotency-key 헤더 |
| **AuthStore** | 토큰/세션 저장(localStorage), bootstrapAutoLogin, clear |
| **SSEClientBase** | EventSource 래퍼, onEvent/onError, 자동 재연결 + 재연결 시 스냅샷 재조회 콜백(Q9) |
| **UIKit** | 큰 터치 타깃 버튼(≥50px), Modal, Badge, Toast, 상태 색상(대기중=노랑/준비중=파랑/완료=초록) |

---

## 3. 폼 검증 규칙 (클라이언트)

| 폼 | 규칙 |
|----|------|
| 테이블 로그인 | 번호/비번 필수 |
| 메뉴 등록/수정 | name/price/category 필수, price 숫자·1,000~100,000, image_url 형식 |
| 테이블 설정 | 번호 필수, 비번 4~10자리 |
| 장바구니 수량 | 1~99, 0이면 항목 제거 |

> 클라이언트 검증은 UX용. 최종 검증·금액 계산은 서버 권위(Q5).

---

## 4. 상태 관리 전략 (Q8)

- **CustomerAuthContext / AdminAuthContext**: 인증 상태.
- **CartContext**: 장바구니, `useEffect`로 localStorage 동기화, 새로고침 복원.
- **SSE 훅**(`useOrderStream`, `useDashboardStream`): 연결/이벤트/재연결·오프라인 배너 상태.
- 서버 데이터는 컴포넌트 로컬 상태 + SSE 증분 갱신. 전역 라이브러리(Redux) 미사용.

---

## 5. 주요 사용자 상호작용 흐름

1. **주문**: MenuList → Detail(추가) → CartDrawer(수량) → OrderConfirm → OrderSubmit(멱등키, 재시도) → OrderSuccess(5초) → MenuList.
2. **관리자 처리**: Dashboard(SSE 신규 강조) → TableCard 클릭 → DetailPanel → 상태 변경(SSE로 고객 반영) / 삭제 / 세션 종료.
3. **오프라인**: SSE 끊김 감지 → 오프라인 배너 + 마지막 데이터 유지 → 재연결 시 대시보드 스냅샷 재조회.

---

**상태**: 검토 대기
