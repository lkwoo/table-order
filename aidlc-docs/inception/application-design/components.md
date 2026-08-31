# Components - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Application Design
**아키텍처**: 레이어드 (Router → Service → Repository), 도메인별 서비스, 단일 React 앱(라우트 분리)

---

## 아키텍처 개요

```
[React SPA]  ──REST/JSON──▶  [FastAPI Routers]  ──▶  [Services (도메인별)]  ──▶  [Repositories]  ──▶  [PostgreSQL]
 /customer                         │                        │
 /admin        ◀──SSE(push)────────┴──[EventBroker(인메모리)]◀┘
```

- **Backend**: FastAPI, 3계층(Router / Service / Repository)
- **Frontend**: 단일 React 앱, 라우트로 고객(/customer)·관리자(/admin) 분리
- **실시간**: 인메모리 EventBroker + 대상별 SSE 엔드포인트
- **인증**: FastAPI Dependency 가드 (관리자 JWT / 고객 테이블 세션 토큰)
- **DB 접근**: Repository 패턴 + 트랜잭션 경계는 Service가 관리

---

## 1. 백엔드 컴포넌트

### 1.1 Router 계층 (API 진입점)

| 컴포넌트 | 목적 | 관련 스토리 | 인증 |
|---------|------|-----------|------|
| **AuthRouter** | 관리자 로그인, 고객 테이블 로그인/자동로그인 | A1, C1, C2 | 공개(로그인), 이후 토큰 |
| **MenuRouter** | 메뉴 조회(고객/관리자), 메뉴 CRUD, 순서 조정 | C3, C4, A9-A13 | 고객 세션 / 관리자 JWT |
| **CartRouter** | (선택) 서버측 검증용 — 장바구니는 클라이언트 localStorage 주력 | C6-C9 | 고객 세션 |
| **OrderRouter** | 주문 생성, 현재 세션 주문 조회 | C10, C11, C12 | 고객 세션 |
| **AdminOrderRouter** | 주문 상세 조회, 상태 변경, 주문 삭제 | A3, A4, A6 | 관리자 JWT |
| **TableRouter** | 테이블 초기 설정, 세션 종료, 과거 이력 조회 | A5, A7, A8 | 관리자 JWT |
| **DashboardRouter** | 대시보드 데이터 조회 (테이블 카드 그리드) | A2 | 관리자 JWT |
| **SSERouter** | 고객/관리자 SSE 스트림 엔드포인트 | C11, A2, A4 | 세션/JWT |

### 1.2 Service 계층 (비즈니스 오케스트레이션)

> 상세 정의는 `services.md` 참고. 여기서는 컴포넌트로서의 책임만 요약.

| 컴포넌트 | 목적 |
|---------|------|
| **AuthService** | 관리자 JWT 발급/검증, 고객 테이블 세션 토큰 발급/검증, bcrypt 해싱 |
| **MenuService** | 메뉴 조회(카테고리별, display_order 정렬) |
| **MenuManagementService** | 메뉴 CRUD + 노출 순서 조정, 데이터 검증 |
| **OrderService** | 주문 생성, 현재 세션 주문 조회, 세션 격리 필터링 |
| **OrderAdminService** | 주문 상태 전이, 주문 삭제, 테이블 총액 재계산 |
| **TableSessionService** | 테이블 초기 설정, 세션 종료(이력 이동 트랜잭션), 과거 이력 조회 |
| **DashboardService** | 테이블별 카드 데이터 집계 |
| **EventBroker** | 인메모리 pub/sub — 이벤트를 SSE 구독자에게 push |

### 1.3 Repository 계층 (데이터 접근)

| 컴포넌트 | 대응 엔티티 |
|---------|-----------|
| **StoreRepository** | Store |
| **AdminRepository** | Admin |
| **TableRepository** | Table |
| **TableSessionRepository** | TableSession |
| **MenuRepository** | Menu, MenuCategory |
| **OrderRepository** | Order, OrderItem |
| **OrderHistoryRepository** | OrderHistory |

### 1.4 공통/횡단 컴포넌트

| 컴포넌트 | 목적 |
|---------|------|
| **AuthGuard (Dependencies)** | `get_current_admin`, `get_current_table_session` — 요청별 인증 검증 |
| **RetryHandler** | 네트워크 오류 시 자동 재시도(최대 3회) — 주로 클라이언트, 서버측 멱등성 보조 |
| **Validator** | 입력 검증 (필수 필드, 가격 범위 등) — Pydantic 스키마 기반 |
| **DBSession/UoW** | SQLAlchemy 세션·트랜잭션 경계 관리 |

---

## 2. 프론트엔드 컴포넌트 (단일 React 앱)

### 2.1 고객 앱 (`/customer`)

| 컴포넌트 | 목적 | 스토리 |
|---------|------|--------|
| **CustomerAppShell** | 라우팅, 자동 로그인 부트스트랩 | C1 |
| **TableLoginView** | 초기 설정 로그인 폼 | C2 |
| **MenuListView** | 카테고리별 메뉴 그리드 | C3 |
| **MenuDetailModal** | 메뉴 상세(이미지/명/가격/설명) | C4 |
| **CartComponent** | 장바구니 추가/수량/제거, localStorage 동기화 | C6, C7, C8 |
| **OrderConfirmView** | 주문 전 최종 확인 | C9 |
| **OrderSubmitView** | 주문 확정, 주문번호 표시, 5초 후 메뉴로 리다이렉트 | C10 |
| **OrderHistoryView** | 현재 세션 주문 내역 + SSE 실시간 상태 | C11, C12 |
| **CustomerSSEClient** | `/sse/orders` 구독, 상태 업데이트 반영 | C11 |

### 2.2 관리자 앱 (`/admin`)

| 컴포넌트 | 목적 | 스토리 |
|---------|------|--------|
| **AdminAppShell** | 라우팅, JWT 검증/자동 로그인 | A1 |
| **AdminLoginView** | 매장ID/사용자명/비밀번호 로그인 | A1 |
| **DashboardView** | 테이블 카드 그리드, 신규 주문 강조 | A2 |
| **TableOrderDetailPanel** | 테이블 상세 주문 + 상태 변경 | A3, A4 |
| **OrderDeleteControl** | 주문 삭제 확인 팝업 | A6 |
| **TableSetupModal** | 테이블 초기 설정 | A5 |
| **SessionEndControl** | 세션 종료 확인 팝업 | A7 |
| **OrderHistoryModal** | 과거 이력 조회 + 날짜 필터 | A8 |
| **MenuManagementView** | 메뉴 CRUD + 순서 조정(드래그앤드롭) | A9-A13 |
| **AdminSSEClient** | `/sse/dashboard` 구독, 오프라인 배너 + 재연결 동기화 | A2 |

### 2.3 공용 프론트엔드 컴포넌트

| 컴포넌트 | 목적 |
|---------|------|
| **ApiClient** | REST 호출 래퍼, 인증 헤더 주입, 자동 재시도(3회) |
| **AuthStore** | 토큰/세션 상태 관리 (localStorage 연동) |
| **SSEClientBase** | EventSource 래퍼, 재연결·오프라인 감지 공통 로직 |
| **UI Kit** | 버튼/모달/배지 등 공용 UI (대형 터치 타깃) |

---

## 3. 컴포넌트 인터페이스 원칙

- **Router → Service**: Router는 요청 파싱·인증·응답 직렬화만 담당, 비즈니스 로직은 Service 위임
- **Service → Repository**: Service가 트랜잭션 경계 소유, Repository는 순수 CRUD
- **Service → EventBroker**: 상태를 변경하는 Service는 커밋 후 도메인 이벤트 발행
- **Frontend → Backend**: REST(요청/응답) + SSE(서버 push) 분리
- **세션 격리**: OrderService의 모든 조회는 `session_id` 필터 강제 (C12)

---

**작성일**: 2026-08-31
**상태**: 검토 대기
**다음 문서**: `component-methods.md`
