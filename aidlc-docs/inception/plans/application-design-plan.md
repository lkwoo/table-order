# Application Design Plan - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Application Design
**목적**: 고수준 컴포넌트 식별 및 서비스 레이어 설계를 위한 실행 계획 + 설계 결정 질문

---

## 개요

이 단계는 **고수준 컴포넌트 식별과 서비스 레이어 설계**에 집중합니다.
- 주요 기능 컴포넌트와 책임 식별
- 컴포넌트 인터페이스(메서드 시그니처) 정의
- 오케스트레이션용 서비스 레이어 설계
- 컴포넌트 의존성 및 통신 패턴 정립

> **참고**: 상세 비즈니스 로직 설계는 이후 **Functional Design(CONSTRUCTION 단계, Unit별)**에서 진행합니다.

**컨텍스트 요약**:
- 기술 스택: FastAPI(백엔드) + React(프론트엔드) + PostgreSQL + SSE + JWT
- 24개 User Stories (고객 11, 관리자 13)
- 9개 엔티티 (Store, Admin, Table, Menu, Order, OrderHistory, MenuCategory, TableSession, OrderItem)
- Extension: Property-Based Testing만 활성

---

# PART 1: PLANNING - 실행 체크리스트

## Step 1: 컨텍스트 분석 ✅
- [x] requirements.md 분석
- [x] stories.md 분석 (24개 스토리)
- [x] 핵심 비즈니스 역량 식별 (인증, 메뉴, 주문, 실시간 모니터링, 테이블/세션 관리)

## Step 2: 설계 결정 질문 답변 (아래 PART 2) ✅
- [x] 모든 [Answer]: 태그 작성 완료 (전부 A/권장, 모호성 없음)

## Step 3: 설계 산출물 생성 (답변 승인 후) ✅
- [x] `components.md` — 컴포넌트 정의 및 고수준 책임
- [x] `component-methods.md` — 메서드 시그니처 (I/O 타입)
- [x] `services.md` — 서비스 정의 및 오케스트레이션 패턴
- [x] `component-dependency.md` — 의존성 매트릭스 및 통신 패턴, 데이터 흐름
- [x] `application-design.md` — 위 문서 통합본
- [x] 설계 완전성/일관성 검증

---

# PART 2: 설계 결정 질문 (Design Decisions)

아래 각 질문의 `[Answer]:` 태그 뒤에 답변을 작성해주세요. 각 질문에는 제가 권장하는 기본값을 표시했으니, 그대로 진행하려면 "권장" 또는 해당 옵션 문자를 적어주시면 됩니다.

---

## Q1. 백엔드 아키텍처 스타일 (Component Identification)

FastAPI 백엔드의 컴포넌트를 어떻게 조직할까요?

- **A) 레이어드 아키텍처 (Router → Service → Repository)** ⭐권장
  - API 라우터 / 비즈니스 서비스 / 데이터 접근(Repository) 3계층 분리
  - 장점: 표준적, 테스트 용이(PBT와 궁합 좋음), 관심사 분리 명확
- **B) 도메인 모듈형 (기능별 모듈: auth, menu, order, table, ...)**
  - 각 도메인이 자체 router/service/model을 포함
- **C) A + B 혼합 (도메인 모듈 내부에 레이어 적용)**

[Answer]: A

---

## Q2. 프론트엔드 앱 분리 (Component Identification)

고객용 UI(태블릿)와 관리자용 UI(대시보드)를 어떻게 구성할까요?

- **A) 단일 React 앱, 라우트로 분리 (/customer, /admin)** ⭐권장
  - 하나의 빌드, 공용 컴포넌트 재사용 용이, 프로토타입에 적합
- **B) 완전히 분리된 2개 React 앱**
  - 독립 배포 가능하나 프로토타입 범위에는 과함

[Answer]: A

---

## Q3. 서비스 레이어 경계 (Service Layer Design)

백엔드 서비스를 어떤 단위로 나눌까요? (레이어드 아키텍처 가정)

- **A) 도메인별 서비스** ⭐권장
  - AuthService, MenuService, OrderService, TableSessionService, DashboardService(SSE), MenuManagementService 등
- **B) 더 굵은 단위 (CustomerService / AdminService 2개)**
- **C) 기타 (설명)**

[Answer]: A

---

## Q4. 실시간(SSE) 통신 설계 (Component Dependencies)

SSE 브로드캐스트를 어떻게 처리할까요?

- **A) 인메모리 이벤트 브로커/펍섭 (단일 서버 인스턴스)** ⭐권장
  - 주문 생성/상태변경 시 인메모리로 구독자에게 push. 10-20 테이블 규모에 충분, 프로토타입 적합
- **B) 외부 메시지 브로커(Redis Pub/Sub 등) 도입**
  - 확장성↑ 하지만 인프라 복잡도↑ (현재 범위 초과 가능)

[Answer]: A

---

## Q5. SSE 채널 분리 방식 (Service Layer Design)

고객(주문 상태 업데이트)과 관리자(신규 주문/대시보드) 대상 SSE를 어떻게 구성할까요?

- **A) 대상별 엔드포인트 분리** ⭐권장
  - 고객: `/sse/orders?session_id=...` (자기 세션 이벤트만)
  - 관리자: `/sse/dashboard` (매장 전체 이벤트, JWT 인증)
- **B) 단일 엔드포인트 + 클라이언트 필터링**

[Answer]: A

---

## Q6. 인증/인가 처리 위치 (Design Patterns)

두 종류의 인증(고객 테이블 세션 토큰, 관리자 JWT)을 어떻게 처리할까요?

- **A) FastAPI 의존성(Dependency Injection) 기반 인증 미들웨어/가드** ⭐권장
  - `get_current_admin`(JWT 검증), `get_current_table_session`(세션 토큰 검증) 의존성으로 분리
- **B) 단일 통합 미들웨어에서 분기 처리**

[Answer]: A

---

## Q7. 세션 종료 트랜잭션 처리 (Component Methods / Service)

테이블 세션 종료(A7: 현재 주문 → 과거 이력 이동, 세션 리셋)의 정합성을 어떻게 보장할까요?

- **A) 단일 DB 트랜잭션 내에서 이동+리셋+새 세션 생성 원자적 처리** ⭐권장
  - Order → OrderHistory 복사/이동, 현재 주문 삭제, 새 TableSession 생성을 하나의 트랜잭션으로
- **B) 별도 단계로 처리 (실패 시 보상 로직)**

[Answer]: A

---

## Q8. 과거 이력 저장 모델 (Component Identification)

주문 이력(OrderHistory)을 어떻게 저장할까요?

- **A) 별도 OrderHistory 테이블로 이동(복사 후 원본 삭제)** ⭐권장
  - 요구사항 6.1이 OrderHistory를 별도 엔티티로 정의. 현재 주문과 과거 이력을 물리적으로 분리
- **B) Order 테이블에 상태 플래그(archived)만 추가**
  - 단순하지만 현재/과거 조회 쿼리가 섞임

[Answer]: A

---

## Q9. 오프라인 지원 범위 (Design Patterns)

관리자 대시보드 오프라인 동작(요구사항 4.2)의 구현 수준은?

- **A) 클라이언트 캐싱 + 오프라인 배너 + 재연결 자동 동기화 (프론트 중심)** ⭐권장
  - 마지막 수신 데이터를 메모리/localStorage에 유지, SSE 재연결 시 최신 상태 재요청
- **B) 서비스 워커 기반 완전 오프라인 (PWA)**
  - 범위 초과 가능

[Answer]: A

---

## Q10. API 스타일 및 문서화 (Design Patterns)

REST API 규약과 문서화 방식은?

- **A) RESTful + FastAPI 자동 OpenAPI 문서(/docs)** ⭐권장
- **B) 기타 규약 (설명)**

[Answer]: A

---

# PART 3: 다음 지침

1. 위 **Q1~Q10의 모든 [Answer]: 태그**에 답변해주세요 (권장값 그대로 가려면 "권장"이라고만 적으셔도 됩니다).
2. 모든 답변이 완료되면 알려주세요.
3. 답변 검토 후 모호한 부분이 있으면 후속 질문을 드립니다.
4. 확정되면 Application Design 산출물(components.md 등 5종)을 생성합니다.

---

**작성일**: 2026-08-31
**상태**: 답변 완료 → 산출물 생성 완료 (검토 대기)
