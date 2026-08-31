# Component Dependency - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Application Design

---

## 1. 레이어 의존 방향

```
Frontend (React SPA)
      │  REST(JSON) / SSE
      ▼
Router 계층  ──depends──▶  AuthGuard(Dependencies)
      │
      ▼
Service 계층 ──depends──▶  EventBroker (쓰기 서비스만)
      │
      ▼
Repository 계층
      │
      ▼
PostgreSQL (SQLAlchemy)
```

- 의존은 **위→아래 단방향**. Repository는 Service를 모른다. Service는 Router를 모른다.
- EventBroker는 Service에서 참조되지만 역방향 의존 없음(SSERouter가 구독자로 연결).

---

## 2. 백엔드 의존성 매트릭스

행(호출자) → 열(피호출자). ✅ = 의존.

| ↓호출자 \ 피호출자→ | AuthSvc | MenuSvc | MenuMgmtSvc | OrderSvc | OrderAdminSvc | TableSessSvc | DashboardSvc | EventBroker | Repos |
|---|---|---|---|---|---|---|---|---|---|
| **AuthRouter** | ✅ | | | | | | | | |
| **MenuRouter** | | ✅ | ✅ | | | | | | |
| **OrderRouter** | | | | ✅ | | | | | |
| **AdminOrderRouter** | | | | | ✅ | | | | |
| **TableRouter** | | | | | | ✅ | | | |
| **DashboardRouter** | | | | | | | ✅ | | |
| **SSERouter** | | | | | | | | ✅ | |
| **AuthService** | | | | | | | | | ✅ |
| **MenuService** | | | | | | | | | ✅ |
| **MenuManagementService** | | | | | | | | | ✅ |
| **OrderService** | | | | | | | | ✅ | ✅ |
| **OrderAdminService** | | | | | | | | ✅ | ✅ |
| **TableSessionService** | | | | | | | | ✅ | ✅ |
| **DashboardService** | | | | | | | | | ✅ |
| **AuthGuard** | ✅ | | | | | | | | |

모든 Router는 요청 인증을 위해 **AuthGuard**에 의존(표에서 생략, 아래 인증 매핑 참조).

---

## 3. 인증 가드 매핑

| Router | 가드 | 토큰 유형 |
|--------|------|----------|
| AuthRouter (로그인) | 없음(공개) | - |
| MenuRouter (고객 조회) | `get_current_table_session` | 세션 토큰 |
| MenuRouter (관리 CRUD) | `get_current_admin` | JWT |
| OrderRouter | `get_current_table_session` | 세션 토큰 |
| AdminOrderRouter, TableRouter, DashboardRouter | `get_current_admin` | JWT |
| SSERouter `/sse/orders` | 세션 토큰(쿼리/헤더) | 세션 토큰 |
| SSERouter `/sse/dashboard` | `get_current_admin` | JWT |

---

## 4. 통신 패턴

| 관계 | 방식 | 비고 |
|------|------|------|
| Frontend → Backend (명령/조회) | REST/HTTP(JSON) | 동기, 자동 재시도 3회(클라이언트) |
| Backend → Frontend (상태 변화 push) | SSE (EventSource) | 단방향 서버→클라이언트 |
| Service ↔ Repository | 인프로세스 함수 호출 | 동일 트랜잭션 |
| Service → EventBroker | 인프로세스 pub (커밋 후) | 비동기 큐 |
| EventBroker → SSERouter | asyncio 큐 소비 | 구독자별 |

---

## 5. 데이터 흐름도

### 5.1 주문 생성 → 실시간 반영

```
[고객] ─POST /orders─▶ OrderRouter ─▶ OrderService
                                          │  [TX commit]
                                          ├─▶ OrderRepository ─▶ PostgreSQL
                                          └─▶ EventBroker.publish(OrderCreated)
                                                    │
                                                    └─▶ /sse/dashboard ─▶ [관리자 대시보드] (<2초)
```

### 5.2 상태 변경 → 고객+관리자 반영

```
[관리자] ─PATCH status─▶ AdminOrderRouter ─▶ OrderAdminService
                                                 │ [TX commit]
                                                 └─▶ EventBroker.publish(OrderStatusChanged)
                                                       ├─▶ /sse/orders(session) ─▶ [고객 주문내역] (<2초)
                                                       └─▶ /sse/dashboard ─▶ [관리자 대시보드]
```

### 5.3 세션 종료 (원자적)

```
[관리자] ─POST end-session─▶ TableRouter ─▶ TableSessionService
                                               │ [단일 TX]
                                               ├─ OrderHistoryRepo.bulk_insert
                                               ├─ OrderRepo.delete_by_table
                                               └─ TableSessionRepo.create_session
                                               │ [commit or rollback]
                                               └─▶ EventBroker.publish(SessionEnded) ─▶ /sse/dashboard
```

---

## 6. 엔티티 ↔ Repository ↔ Service 매핑

| 엔티티 | Repository | 주 사용 Service |
|--------|-----------|----------------|
| Store | StoreRepository | AuthService |
| Admin | AdminRepository | AuthService |
| Table | TableRepository | TableSessionService |
| TableSession | TableSessionRepository | AuthService, TableSessionService |
| MenuCategory | MenuRepository | MenuService, MenuManagementService |
| Menu | MenuRepository | MenuService, MenuManagementService |
| Order | OrderRepository | OrderService, OrderAdminService, DashboardService |
| OrderItem | OrderRepository | OrderService |
| OrderHistory | OrderHistoryRepository | TableSessionService |

---

## 7. 순환 의존성 점검

- Service 간 직접 호출 없음 → **순환 없음**.
- 실시간 연동은 모두 EventBroker 경유(느슨한 결합) → Service 간 결합도 최소.
- Router는 서로를 호출하지 않음.

✅ 의존성 그래프는 비순환(DAG).

---

## 8. 배포 단위 (참고)

| 단위 | 구성 | 컨테이너 |
|------|------|---------|
| frontend | React 빌드(정적) | nginx 또는 정적 서빙 |
| backend | FastAPI + EventBroker(인메모리) | uvicorn |
| db | PostgreSQL | postgres |

> EventBroker가 인메모리이므로 backend는 **단일 인스턴스** 전제(Q4-A). 다중 인스턴스 확장은 향후 Redis Pub/Sub 도입 시(범위 외).

---

**작성일**: 2026-08-31
**상태**: 검토 대기
**다음 문서**: `application-design.md` (통합본)
