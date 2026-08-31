# Application Design (통합본) - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Application Design
**상태**: 검토 대기

이 문서는 Application Design 단계의 산출물을 통합한 개요입니다. 세부 내용은 아래 개별 문서를 참고하세요.
- [`components.md`](./components.md) — 컴포넌트 정의 및 책임
- [`component-methods.md`](./component-methods.md) — 메서드 시그니처
- [`services.md`](./services.md) — 서비스 정의 및 오케스트레이션
- [`component-dependency.md`](./component-dependency.md) — 의존성/통신/데이터 흐름

---

## 1. 설계 결정 요약 (승인됨)

| # | 결정 | 선택 |
|---|------|------|
| Q1 | 백엔드 아키텍처 | 레이어드 (Router → Service → Repository) |
| Q2 | 프론트엔드 구성 | 단일 React 앱, 라우트 분리 (/customer, /admin) |
| Q3 | 서비스 경계 | 도메인별 서비스 |
| Q4 | SSE 브로드캐스트 | 인메모리 EventBroker (단일 인스턴스) |
| Q5 | SSE 채널 | 대상별 엔드포인트 분리 (고객/관리자) |
| Q6 | 인증 처리 | FastAPI Dependency 가드 (JWT / 세션 토큰) |
| Q7 | 세션 종료 | 단일 DB 트랜잭션 (원자적) |
| Q8 | 이력 저장 | 별도 OrderHistory 테이블 |
| Q9 | 오프라인 | 클라이언트 캐싱 + 재연결 자동 동기화 |
| Q10 | API 스타일 | RESTful + OpenAPI 자동 문서 |

---

## 2. 아키텍처 한눈에 보기

```
┌────────────────────── React SPA ──────────────────────┐
│  /customer (태블릿)          /admin (대시보드)          │
│  MenuList, Cart, Order...    Dashboard, MenuMgmt...     │
│  ApiClient · AuthStore · SSEClientBase                 │
└──────────┬───────────────────────────┬─────────────────┘
       REST │                       SSE │ (push)
            ▼                           ▲
┌───────────────────────── FastAPI ─────────────────────┐
│  Routers ── AuthGuard(JWT/세션)                        │
│     ▼                                                  │
│  Services (도메인별) ──▶ EventBroker(인메모리 pub/sub) │
│     ▼                                                  │
│  Repositories                                          │
└──────────┬─────────────────────────────────────────────┘
           ▼
      PostgreSQL (9 엔티티, 트랜잭션)
```

---

## 3. 컴포넌트 요약

**백엔드**: 8개 Router, 7개 도메인 서비스 + EventBroker, 7개 Repository, AuthGuard/Validator/UoW 횡단 컴포넌트.

**프론트엔드**: 고객 9개 + 관리자 10개 + 공용 4개 컴포넌트 (단일 앱).

**서비스**: AuthService, MenuService, MenuManagementService, OrderService, OrderAdminService, TableSessionService, DashboardService, EventBroker.

---

## 4. 핵심 설계 포인트

1. **실시간(SSE)**: 상태를 바꾸는 서비스는 커밋 후 도메인 이벤트를 발행 → EventBroker → 대상별 SSE 스트림. 고객은 자기 세션 이벤트만, 관리자는 매장 전체.
2. **세션 종료 원자성**: 현재 주문→OrderHistory 이동, 현재 주문 리셋, 새 세션 생성이 단일 트랜잭션. 실패 시 전체 롤백.
3. **세션 격리**: OrderService 조회는 항상 현재 session_id로 필터(C12). 서비스 레벨 강제.
4. **인증 이원화**: 관리자 JWT(16h) / 고객 테이블 세션 토큰. FastAPI 의존성 가드로 분리.
5. **오프라인**: 관리자 대시보드는 마지막 데이터 유지 + 오프라인 배너, 재연결 시 REST 재조회로 갭 보정.
6. **참조 무결성**: 메뉴 삭제 시 과거 이력에는 메뉴명 스냅샷 보존.
7. **결합도**: 서비스 간 직접 호출 없음(EventBroker 경유) → 비순환 의존 그래프.

---

## 5. 요구사항/스토리 커버리지 검증

| 영역 | 스토리 | 담당 컴포넌트 | 커버 |
|------|--------|-------------|------|
| 고객 인증/세션 | C1, C2 | AuthService, AuthGuard, CustomerAppShell | ✅ |
| 메뉴 조회 | C3, C4 | MenuService, MenuListView, MenuDetailModal | ✅ |
| 장바구니 | C6, C7, C8, C9 | CartComponent (localStorage) | ✅ |
| 주문 생성 | C10 | OrderService, OrderSubmitView, EventBroker | ✅ |
| 주문 내역/격리 | C11, C12 | OrderService, OrderHistoryView, CustomerSSEClient | ✅ |
| 관리자 인증 | A1 | AuthService, AdminLoginView | ✅ |
| 실시간 모니터링 | A2, A3, A4 | DashboardService, OrderAdminService, EventBroker, AdminSSEClient | ✅ |
| 테이블 관리 | A5, A6, A7, A8 | TableSessionService, OrderAdminService | ✅ |
| 메뉴 관리 | A9~A13 | MenuManagementService, MenuManagementView | ✅ |
| 성능(<1s/2s) | 전체 | 인메모리 이벤트, 인덱스 조회 | ✅ (설계 반영) |
| 가용성(오프라인) | A2 | AdminSSEClient(캐싱/재동기화) | ✅ |
| 보안(JWT/bcrypt) | A1, A4 | AuthService, AuthGuard | ✅ |
| 데이터 관리(트랜잭션/격리/3개월) | A7, C12, A8 | TableSessionService, OrderHistoryRepository | ✅ |

**커버리지: 24/24 스토리, 요구사항 3.x/4.x 전 항목 매핑 완료.**

---

## 6. 다음 단계

- **Units Generation** (INCEPTION): 위 컴포넌트/서비스를 개발 Unit(데이터 모델, API, 로직)으로 분해.
- 이후 CONSTRUCTION: Functional Design → NFR → Infrastructure → Code Generation → Build & Test.

---

**작성일**: 2026-08-31
**상태**: 검토 대기 (Approval Required)
