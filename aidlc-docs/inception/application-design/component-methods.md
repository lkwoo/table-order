# Component Methods - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Application Design

> **범위**: 메서드 시그니처(이름, 입력/출력 타입, 고수준 목적)만 정의합니다.
> **상세 비즈니스 규칙**(엣지 케이스, 상태 전이 규칙, 검증 로직 등)은 **Functional Design(CONSTRUCTION, Unit별)** 에서 정의합니다.

타입 표기는 개념적(pseudo-Python/Pydantic)이며 구현 시 조정될 수 있습니다.

---

## 1. AuthService

| 메서드 | 시그니처 | 목적 | 스토리 |
|--------|---------|------|--------|
| 관리자 로그인 | `admin_login(store_id: str, username: str, password: str) -> AuthToken` | 자격 검증 후 JWT(16h) 발급 | A1 |
| 관리자 검증 | `verify_admin_token(token: str) -> AdminContext` | JWT 유효성/만료 검증 | A1 |
| 테이블 로그인 | `table_login(table_number: str, password: str) -> SessionToken` | 테이블 자격 검증 후 세션 토큰 발급 | C2 |
| 테이블 세션 검증 | `verify_table_session(token: str) -> TableSessionContext` | 세션 토큰 유효/만료(16h) 검증 | C1, C12 |
| 비밀번호 해싱 | `hash_password(raw: str) -> str` / `verify_password(raw, hashed) -> bool` | bcrypt 해싱/검증 | A1, A5 |

## 2. MenuService (고객용 조회)

| 메서드 | 시그니처 | 목적 | 스토리 |
|--------|---------|------|--------|
| 메뉴 목록 | `list_menus(store_id: str) -> list[MenuByCategory]` | 카테고리별, display_order 정렬 메뉴 반환 | C3 |
| 메뉴 상세 | `get_menu(menu_id: str) -> MenuDetail` | 단일 메뉴 상세(명/가격/설명/이미지) | C4 |

## 3. MenuManagementService (관리자용)

| 메서드 | 시그니처 | 목적 | 스토리 |
|--------|---------|------|--------|
| 관리자 메뉴 목록 | `list_menus_admin(store_id: str) -> list[MenuByCategory]` | 관리 화면용 메뉴 목록 | A9 |
| 메뉴 등록 | `create_menu(store_id: str, data: MenuCreate) -> Menu` | 검증 후 신규 메뉴 생성 | A10 |
| 메뉴 수정 | `update_menu(menu_id: str, data: MenuUpdate) -> Menu` | 필드 수정 | A11 |
| 메뉴 삭제 | `delete_menu(menu_id: str) -> None` | 삭제(과거 이력 참조 무결성 보존) | A12 |
| 순서 조정 | `reorder_menus(category_id: str, ordered_ids: list[str]) -> None` | display_order 일괄 갱신 | A13 |

## 4. OrderService (고객 주문)

| 메서드 | 시그니처 | 목적 | 스토리 |
|--------|---------|------|--------|
| 주문 생성 | `create_order(session_ctx: TableSessionContext, items: list[OrderItemInput]) -> Order` | 주문+주문항목 저장, 이벤트 발행 | C10 |
| 현재 세션 주문 조회 | `list_current_orders(session_ctx: TableSessionContext) -> list[Order]` | 현재 session_id 주문만 시간 역순 | C11, C12 |

## 5. OrderAdminService (관리자 주문 처리)

| 메서드 | 시그니처 | 목적 | 스토리 |
|--------|---------|------|--------|
| 테이블 주문 상세 | `get_table_orders(table_id: str) -> TableOrdersDetail` | 테이블의 현재 주문 상세 | A3 |
| 상태 변경 | `update_order_status(order_id: str, new_status: OrderStatus, admin_ctx) -> Order` | 상태 전이, 이벤트 발행, 로그 기록 | A4 |
| 주문 삭제 | `delete_order(order_id: str, admin_ctx) -> TableTotals` | 삭제 후 테이블 총액 재계산, 이벤트 발행 | A6 |

## 6. TableSessionService

| 메서드 | 시그니처 | 목적 | 스토리 |
|--------|---------|------|--------|
| 테이블 초기 설정 | `setup_table(store_id: str, table_number: str, password: str) -> Table` | 테이블 생성 + 16h 세션, 중복 검사 | A5 |
| 세션 종료 | `end_session(table_id: str, admin_ctx) -> None` | **단일 트랜잭션**: 현재 주문→OrderHistory 이동, 현재 주문 리셋, 새 세션 생성, 이벤트 발행 | A7 |
| 과거 이력 조회 | `list_order_history(table_id: str, date_filter: DateRange \| None) -> list[OrderHistory]` | 3개월 내 과거 주문, 시간 역순 | A8 |

## 7. DashboardService

| 메서드 | 시그니처 | 목적 | 스토리 |
|--------|---------|------|--------|
| 대시보드 데이터 | `get_dashboard(store_id: str) -> list[TableCard]` | 테이블별 총액/최신 주문 n개 집계 | A2 |

각 `TableCard`: `{ table_number, total_amount, recent_orders: list[OrderPreview] }`

## 8. EventBroker (인메모리 pub/sub)

| 메서드 | 시그니처 | 목적 |
|--------|---------|------|
| 발행 | `publish(event: DomainEvent) -> None` | 이벤트를 대상 구독자 큐에 push |
| 구독(관리자) | `subscribe_dashboard(store_id: str) -> AsyncIterator[DomainEvent]` | 매장 전체 이벤트 스트림 |
| 구독(고객) | `subscribe_session(session_id: str) -> AsyncIterator[DomainEvent]` | 해당 세션 이벤트 스트림 |
| 구독 해제 | `unsubscribe(subscriber_id: str) -> None` | 연결 종료 시 정리 |

**DomainEvent 종류**: `OrderCreated`, `OrderStatusChanged`, `OrderDeleted`, `SessionEnded`

## 9. Repository 계층 (대표 메서드)

공통 시그니처 패턴: `get(id)`, `list(**filters)`, `add(entity)`, `update(entity)`, `delete(id)` — SQLAlchemy 세션 주입.

| Repository | 특기 메서드 |
|-----------|-----------|
| **OrderRepository** | `list_by_session(session_id)`, `list_by_table(table_id)`, `sum_total_by_table(table_id)` |
| **OrderHistoryRepository** | `bulk_insert(orders)`, `list_by_table(table_id, date_range)` |
| **MenuRepository** | `list_by_store_ordered(store_id)`, `update_display_orders(pairs)` |
| **TableSessionRepository** | `get_active_by_table(table_id)`, `create_session(table_id, expires_at)` |
| **AdminRepository** | `get_by_credentials(store_id, username)` |

## 10. AuthGuard (FastAPI Dependencies)

| 의존성 | 시그니처 | 목적 |
|--------|---------|------|
| 관리자 가드 | `get_current_admin(authorization: Header) -> AdminContext` | JWT 검증, 실패 시 401 |
| 고객 세션 가드 | `get_current_table_session(x_session_token: Header) -> TableSessionContext` | 세션 토큰 검증, 만료 시 401 |

## 11. Frontend 핵심 메서드 (개념)

| 컴포넌트 | 메서드 | 목적 |
|---------|--------|------|
| **ApiClient** | `request(method, path, body, auth) -> Response` (자동 재시도 3회) | REST 호출 |
| **AuthStore** | `bootstrapAutoLogin()`, `saveToken()`, `clear()` | 토큰/세션 상태 (C1, A1) |
| **CartComponent** | `addItem()`, `changeQty()`, `removeItem()`, `clear()`, `computeTotal()` | localStorage 동기화 (C6-C8) |
| **SSEClientBase** | `connect()`, `onEvent()`, `onDisconnect()`, `reconnect()` | SSE 구독/재연결 (C11, A2) |

---

**작성일**: 2026-08-31
**상태**: 검토 대기
**다음 문서**: `services.md`
