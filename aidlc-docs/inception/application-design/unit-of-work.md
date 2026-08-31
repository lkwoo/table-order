# Unit of Work - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Units Generation
**배포 모델**: 모놀리식 단일 서비스 (논리 모듈로 분해)
**그룹핑 기준**: 비즈니스 도메인 / 역량

---

## 정의

- 이 프로젝트는 **모놀리식**입니다: 백엔드 1개(FastAPI) + 프론트 1개(React) + PostgreSQL.
- 따라서 각 **Unit = 논리 모듈**(독립 배포 단위가 아님). Application Design의 도메인별 서비스 경계를 그대로 따릅니다.
- 프론트엔드는 빌드/배포 특성이 달라 **독립 Unit**으로 취급하고 내부를 고객/관리자 모듈로 구분합니다.
- 공유 요소(인증 가드, EventBroker, DB/모델, 공용 유틸)는 **Core Unit**으로 분리합니다.

---

## Unit 목록

| Unit ID | 이름 | 유형 | 책임 | 관련 서비스/컴포넌트 | Sprint |
|---------|------|------|------|---------------------|--------|
| **U0** | Core / Shared (백엔드 기반) | 백엔드 모듈 | 설정, DB 세션/UoW, ORM 모델(9 엔티티), AuthGuard, EventBroker, 공용 Validator | DBSession, AuthGuard, EventBroker, Validator | S1 |
| **U1** | Auth (인증) | 백엔드 모듈 | 관리자 JWT, 고객 테이블 세션 토큰, bcrypt | AuthService, AuthRouter | S1 |
| **U2** | Menu (메뉴 조회) | 백엔드 모듈 | 고객용 메뉴 조회(카테고리/정렬) | MenuService, MenuRouter(고객) | S1 |
| **U3** | Order (주문 - 고객) | 백엔드 모듈 | 주문 생성, 현재 세션 주문 조회, 세션 격리, 이벤트 발행 | OrderService, OrderRouter | S1 |
| **U4** | Realtime & Dashboard | 백엔드 모듈 | 대시보드 집계, 관리자 주문 처리(상태/삭제), SSE 스트림 | DashboardService, OrderAdminService, SSERouter, AdminOrderRouter | S1 |
| **U5** | Table & Session (테이블 관리) | 백엔드 모듈 | 테이블 초기 설정, 세션 종료(원자적 이력 이동), 과거 이력 조회 | TableSessionService, TableRouter | S1 |
| **U6** | Menu Management (메뉴 관리) | 백엔드 모듈 | 메뉴 CRUD + 노출 순서 조정, 검증 | MenuManagementService, MenuRouter(관리) | S2 |
| **U7** | Frontend (React 앱) | 프론트 단위 | 고객 모듈(/customer) + 관리자 모듈(/admin) + 공용(ApiClient/AuthStore/SSEClientBase) | 모든 View/Component | S1~S2 |

---

## Unit별 스토리 배정

| Unit | 배정 스토리 |
|------|-----------|
| **U0** Core | (횡단 — 모든 스토리 지원, 직접 스토리 없음) |
| **U1** Auth | A1, C1, C2 |
| **U2** Menu | C3, C4 |
| **U3** Order | C6, C7, C8, C9(클라이언트), C10, C11, C12 (서버측: C10 생성, C11/C12 조회·격리) |
| **U4** Realtime & Dashboard | A2, A3, A4, A6 |
| **U5** Table & Session | A5, A7, A8 |
| **U6** Menu Management | A9, A10, A11, A12, A13 |
| **U7** Frontend | 전 스토리 UI (C1-C12, A1-A13) |

> C6~C9 장바구니는 클라이언트(localStorage) 중심이므로 UI 측면은 U7, 서버 개입은 주문 생성(U3)에서만 발생.

**커버리지 확인**: 24개 스토리 전부 하나 이상의 Unit에 배정됨 ✅ (누락 없음).

---

## 코드 조직 전략 (Greenfield, 모놀리식)

```
table-order/
├── backend/
│   ├── app/
│   │   ├── core/            # U0: config, db(session/UoW), security(가드), events(EventBroker), models(ORM 9엔티티), schemas 공통
│   │   ├── auth/            # U1: router, service, repository, schemas
│   │   ├── menu/            # U2: router(고객 조회), service, repository
│   │   ├── order/           # U3: router, service, repository (Order/OrderItem)
│   │   ├── realtime/        # U4: dashboard/admin-order router, service, sse endpoints
│   │   ├── table/           # U5: router, service, repository (Table/TableSession/OrderHistory)
│   │   ├── menu_admin/      # U6: router(관리 CRUD/순서), service
│   │   └── main.py          # FastAPI 앱 조립, 라우터 등록
│   ├── tests/               # 속성 기반 테스트 포함 (PBT 활성)
│   ├── pyproject.toml / requirements.txt
│   └── Dockerfile
├── frontend/                # U7
│   ├── src/
│   │   ├── customer/        # 고객 뷰/컴포넌트
│   │   ├── admin/           # 관리자 뷰/컴포넌트
│   │   ├── shared/          # ApiClient, AuthStore, SSEClientBase, UI Kit
│   │   └── main.tsx / App.tsx (라우팅 /customer, /admin)
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml       # backend + frontend + postgres
└── aidlc-docs/              # (문서, 코드 아님)
```

- 백엔드는 도메인별 패키지, 각 패키지 내부에 router/service/repository/schema 배치(레이어드).
- 모델(ORM)은 U0/core에 통합(엔티티 간 관계 정의가 한 곳에 모여야 정합성 유지 용이).
- 프론트는 customer/admin/shared 3분할.

---

## 검증

| 항목 | 상태 |
|------|------|
| 모든 스토리가 Unit에 배정되었는가? | ✅ 24/24 |
| Unit 경계가 Application Design 서비스와 일치하는가? | ✅ |
| 공유 요소가 Core로 분리되었는가? | ✅ U0 |
| 순환 의존성 없이 배치 가능한가? | ✅ (unit-of-work-dependency.md 참고) |
| Greenfield 코드 조직 전략 문서화? | ✅ |

---

**작성일**: 2026-08-31
**상태**: 검토 대기
