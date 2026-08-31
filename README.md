# 테이블오더 (Table Order)

식당 테이블에서 고객이 QR/태블릿으로 직접 메뉴를 주문하고, 관리자가 실시간
대시보드로 주문을 관리하는 웹 서비스. **AI-DLC(AI-Driven Development Life Cycle)**
방법론을 따라 요구사항 → 설계 → 코드 → 검증까지 단계별로 개발되었다.

이 README는 **개발 결과물 안내**인 동시에, **AI-DLC가 각 단계에서 무엇을 만들고 왜
만들었는지**를 따라 읽을 수 있는 가이드다. 산출물의 원본은 모두
[`aidlc-docs/`](aidlc-docs/) 에 있고, 단계별 승인·프롬프트 이력은
[`aidlc-docs/audit.md`](aidlc-docs/audit.md) 에 시간순으로 기록되어 있다.

---

## 1. AI-DLC 한눈에 보기

AI-DLC는 소프트웨어를 세 개의 큰 **Phase**로 나누고, 각 Phase 안에서 여러 **Stage**를
순서대로 밟는다. 각 Stage는 **문서(계획·설계)를 먼저 만들고 → 사용자 승인을 받은 뒤 →
다음 Stage로 넘어가는** 게이트 구조다. 모든 규칙의 원본 정의는 [`CLAUDE.md`](CLAUDE.md)
와 [`.aidlc-rule-details/`](.aidlc-rule-details/) 에 있다.

| Phase | 목적 | 질문 | 결과물 위치 |
| --- | --- | --- | --- |
| 🔵 **INCEPTION** | 무엇을·왜 만드는가 | WHAT / WHY | `aidlc-docs/inception/` |
| 🟢 **CONSTRUCTION** | 어떻게 만드는가 | HOW | `aidlc-docs/construction/` + 실제 코드 |
| 🟡 **OPERATIONS** | 어떻게 배포·운영하는가 | DEPLOY / RUN | (플레이스홀더) |

두 개의 문서는 전 과정에 걸쳐 계속 갱신된다:

- [`aidlc-docs/aidlc-state.md`](aidlc-docs/aidlc-state.md) — **진행 상태판**. 어떤 Stage가
  끝났고 지금 어디인지, 기술 결정과 확장(Extension) 설정을 추적한다.
- [`aidlc-docs/audit.md`](aidlc-docs/audit.md) — **감사 로그**. 사용자의 모든 입력과
  승인, AI의 응답을 원문 그대로 시간순 기록한다.

> **입력물(사람이 준 씨앗):** [`requirements/table-order-requirements.md`](requirements/table-order-requirements.md),
> [`requirements/constraints.md`](requirements/constraints.md) — AI-DLC가 시작하기 전에
> 사람이 작성한 원본 요구사항과 제약. 이후 모든 산출물의 출발점이다.

---

## 2. 개발 여정 — 단계별 산출물과 역할

아래 순서는 실제 git 히스토리(`git log --reverse`)의 진행 순서와 일치한다.

### 🔵 INCEPTION — 무엇을 왜 만들 것인가

#### ① Workspace Detection (작업공간 탐지)
빈 프로젝트인지(그린필드) 기존 코드가 있는지(브라운필드) 판별. 여기서는 **그린필드**로
판정되어 Reverse Engineering은 건너뛰었다.
- `aidlc-docs/aidlc-state.md`, `aidlc-docs/audit.md` — 최초 생성(상태판·감사로그 시작)

#### ② Requirements Analysis (요구사항 분석)
원본 요구사항을 분석해 모호한 점을 사용자에게 질문하고, 확정된 요구사항 명세로 정리.
- `inception/requirements/requirement-verification-questions.md` — AI가 사용자에게 던진
  확인 질문과 그 답변
- `inception/requirements/requirements.md` — **확정 요구사항 명세**(기능/비기능, MVP 범위)

#### ③ User Stories (사용자 스토리)
"누가 · 무엇을 · 왜" 관점으로 요구사항을 스토리화. 페르소나와 스토리-기능 매트릭스 작성.
- `inception/plans/user-stories-assessment.md` — 스토리 작성이 필요한지 판단한 근거
- `inception/plans/story-generation-plan.md` — 스토리 생성 계획과 사용자 답변
- `inception/user-stories/personas.md` — 페르소나 2종(고객 / 관리자)
- `inception/user-stories/stories.md` — **사용자 스토리 24개**(고객 11 · 관리자 13)
- `inception/user-stories/story-matrix.md` — 스토리 ↔ 기능 매핑 매트릭스

#### ④ Workflow Planning (워크플로 계획)
이후 어떤 Stage를 어떤 깊이로 실행할지 전체 실행 계획 수립.
- `inception/plans/execution-plan.md` — **전체 실행 로드맵**(실행/생략 Stage 결정)

#### ⑤ Application Design (애플리케이션 설계)
컴포넌트·서비스·메서드·의존성 등 논리 설계. "무엇을 만들지"를 구조로 확정.
- `inception/plans/application-design-plan.md` — 설계 계획
- `inception/application-design/application-design.md` — 설계 개요
- `inception/application-design/components.md` — 컴포넌트 목록과 책임
- `inception/application-design/component-methods.md` — 컴포넌트별 메서드 시그니처
- `inception/application-design/component-dependency.md` — 컴포넌트 간 의존 관계
- `inception/application-design/services.md` — 서비스 계층 정의

#### ⑥ Units Generation (작업 단위 분해)
전체 시스템을 독립적으로 만들 수 있는 **Unit(작업 단위) 8개**로 분해. 이후 CONSTRUCTION은
이 단위별로 반복 실행된다.
- `inception/plans/unit-of-work-plan.md` — 분해 계획
- `inception/application-design/unit-of-work.md` — **8개 Unit 정의**(U0~U7)
- `inception/application-design/unit-of-work-dependency.md` — Unit 간 의존(빌드 순서)
- `inception/application-design/unit-of-work-story-map.md` — Unit ↔ 스토리 매핑

### 🟢 CONSTRUCTION — 어떻게 만들 것인가

CONSTRUCTION은 **Unit별 루프**(설계→코드)를 돈 뒤, 마지막에 전체 Build & Test를 한다.

#### ⑦ Functional Design (기능 설계, Unit별)
Unit마다 도메인 엔티티·업무 규칙·업무 로직 모델을 상세화.
- `construction/plans/functional-design-plan.md` — 8개 Unit 기능 설계 계획
- `construction/{U0~U7}/functional-design/*.md` — Unit별 기능 설계 문서
  - `business-rules.md` — 업무 규칙(불변식·검증 규칙)
  - `domain-entities.md` (U0) — 도메인 엔티티/데이터 모델
  - `business-logic-model.md` — 업무 로직 흐름
  - `frontend-components.md` (U7) — 프런트엔드 화면/컴포넌트 설계

#### ⑧ NFR Requirements (비기능 요구사항)
성능·보안·확장성 요구와 **기술 스택 결정**을 프로젝트 수준으로 확정.
- `construction/plans/nfr-requirements-plan.md` — 계획
- `construction/nfr-requirements/nfr-requirements.md` — 비기능 요구사항
- `construction/nfr-requirements/tech-stack-decisions.md` — **기술 스택 결정 근거**
  (FastAPI · React · PostgreSQL · SSE · JWT · Docker)

#### ⑨ NFR Design (비기능 설계)
비기능 요구를 만족시키는 설계 패턴과 논리 컴포넌트 정의.
- `construction/plans/nfr-design-plan.md` — 계획
- `construction/nfr-design/nfr-design-patterns.md` — 설계 패턴
  (EventBroker · AuthGuard · Unit-of-Work · 캐시)
- `construction/nfr-design/logical-components.md` — 논리 컴포넌트 정의

#### ⑩ Infrastructure Design (인프라 설계)
배포 구조와 컨테이너 구성 설계.
- `construction/plans/infrastructure-design-plan.md` — 계획
- `construction/infrastructure-design/infrastructure-design.md` — 인프라 설계
- `construction/infrastructure-design/deployment-architecture.md` — 배포 아키텍처
- `construction/shared-infrastructure.md` — **공유 인프라 규약**
  (Docker Compose db+backend+frontend, 단일 워커 제약, 디렉터리 구조)

#### ⑪ Code Generation (코드 생성)
설계를 실제 코드로 구현. **문서(aidlc-docs)가 아니라 워크스페이스 루트에 코드가 생성된다.**
- `construction/plans/code-generation-plan.md` — 코드 생성 계획
- `construction/{U0~U7}/code/code-summary.md` — Unit별 생성 코드 요약(문서)
- **실제 코드**(워크스페이스 루트):
  - [`backend/`](backend/) — FastAPI 앱(`app/`), 테스트(`tests/`), `alembic/`, `Dockerfile`
  - [`frontend/`](frontend/) — React + TypeScript + Vite (`src/`)
  - [`docker-compose.yml`](docker-compose.yml), [`.env.example`](.env.example), `.gitignore`

#### ⑫ Build and Test (빌드·테스트)
전체 빌드/테스트 지침을 문서화하고 테스트를 실행.
- `construction/build-and-test/build-instructions.md` — 빌드 절차
- `construction/build-and-test/unit-test-instructions.md` — 단위 테스트 지침
- `construction/build-and-test/integration-test-instructions.md` — 통합 테스트 지침
- `construction/build-and-test/performance-test-instructions.md` — 성능 테스트 지침
- `construction/build-and-test/build-and-test-summary.md` — 결과 요약
- **실제 테스트/검증**: `backend/tests/`, `backend/live_check.py`(실기동 스모크 테스트)

### 🟡 OPERATIONS — 배포·운영 (플레이스홀더)

현행 AI-DLC 워크플로는 Build & Test 이후 종료된다. 배포 실행·모니터링·장애 대응·프로덕션
준비 체크리스트는 향후 확장 범위(Future Scope)로 남는다.
정의: [`.aidlc-rule-details/operations/operations.md`](.aidlc-rule-details/operations/operations.md)

---

## 3. 8개 작업 단위 (Units)

애플리케이션은 다음 8개 Unit으로 분해되어 U0부터 순서대로 구현되었다.

| Unit | 이름 | 역할 | 주요 코드 |
| --- | --- | --- | --- |
| **U0** | core | 공유 기반: 설정·DB·도메인 모델·보안·EventBroker·트랜잭션(UoW) | `backend/app/core/` |
| **U1** | auth | 인증: 관리자 JWT · 테이블 세션 토큰 · bcrypt | `backend/app/auth/` |
| **U2** | menu | 고객 메뉴 조회(카테고리별) | `backend/app/menu/` |
| **U3** | order | 주문 생성/조회, 총액 재계산, idempotency | `backend/app/order/` |
| **U4** | realtime | 실시간 알림(SSE) — 주문/대시보드 스트림 | `backend/app/realtime/` |
| **U5** | table | 테이블·테이블 세션 관리, 세션 종료/이력 | `backend/app/table_session/` |
| **U6** | menu-management | 관리자 메뉴/카테고리 CRUD·정렬, 대시보드, 주문 상태 전이 | `backend/app/menu_mgmt/` |
| **U7** | frontend | React 화면(고객 주문 · 관리자 대시보드) | `frontend/src/` |

의존/빌드 순서 근거: `aidlc-docs/inception/application-design/unit-of-work-dependency.md`

---

## 4. 제품 개요

### 기술 스택

| 영역 | 스택 |
| --- | --- |
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · PostgreSQL 16 |
| 실시간 | 인프로세스 EventBroker(asyncio) + SSE(Server-Sent Events) |
| Auth | JWT(python-jose) · bcrypt(passlib) |
| Frontend | React 18 · TypeScript · Vite · React Router 6 |
| 테스트 | pytest · Hypothesis(속성 기반 테스트) |
| 배포 | Docker Compose (db · backend · frontend) |

> 백엔드는 인메모리 EventBroker 상태 일관성을 위해 **단일 워커**로 실행한다.

### 아키텍처

계층형 구조: `Router → Service → Repository`. 트랜잭션 경계는 서비스의 Unit-of-Work에서
관리하며, 이벤트는 **커밋 이후에만** 발행한다.

핵심 도메인 규칙:
- 주문 idempotency-key로 중복 제출 방지
- 금액은 서버에서 재계산(클라이언트 값 신뢰 안 함)
- 세션 격리: `TableSession.id` 기준으로 주문 분리
- 메뉴는 소프트 삭제, 주문/이력에는 스냅샷(이름·단가) 보존
- 주문 상태 전이는 단방향 (대기중 → 준비중 → 완료)

인증 경계:
- 관리자 API — `Authorization: Bearer <JWT>` (16시간 세션)
- 고객(테이블) API — `X-Session-Token: <불투명 토큰>` (테이블 세션)

---

## 5. 빠른 시작 (Docker Compose)

```bash
cp .env.example .env      # 필요 시 값 수정
docker compose up --build
```

- 프런트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000  (헬스체크: `/health`)

초기 시드 데이터(첫 기동 시 자동 생성, 멱등):
- 관리자 로그인 — 매장 ID `11111111-1111-1111-1111-111111111111`, 아이디 `admin`, 비밀번호 `admin1234`
- 샘플 메뉴 3개 카테고리 — 메인(김치찌개·된장찌개·제육볶음), 음료(콜라·사이다), 주류(소주·맥주). 음료·주류 메뉴에는 예시 이미지 URL이 포함되어 있다(이미지는 외부 URL 방식 — 파일 업로드 없음). 메뉴/이미지는 관리자 화면 **메뉴 관리**에서 언제든 추가·수정할 수 있다.

## 6. 로컬 개발

### 백엔드

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows (bash: source .venv/Scripts/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --workers 1
```

기본 설정은 `postgresql+psycopg://app:app@db:5432/tableorder`를 가리킨다.
로컬 PostgreSQL이나 `DATABASE_URL` 환경 변수로 조정한다.
(PostgreSQL 없이 빠르게 띄우려면 `DATABASE_URL=sqlite:///./dev.db` — 앱 기동 시 스키마
자동 생성 및 시드가 수행된다.)

### 프런트엔드

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, /api 는 localhost:8000 으로 프록시
npm run build        # tsc 타입체크 + 프로덕션 번들(dist/)
```

## 7. 테스트 & 검증

### 자동 테스트 — pytest + Hypothesis

속성 기반 테스트(Hypothesis)로 7개 핵심 불변식을 검증한다.

```bash
cd backend
.venv/Scripts/python -m pytest        # 17 passed (단위/PBT 13 + 통합 4), 커버리지 ~85%
```

검증하는 불변식:
1. 주문 총액 = Σ(단가 × 수량)
2. 동일 idempotency-key N회 요청 → 주문 1건
3. 세션 격리 (세션 A 조회에 세션 B 주문 없음)
4. 세션 종료 시 합계 보존 (이력 합계 == 종료 전 합계)
5. `완료` 상태에서 이전 상태로의 전이 항상 거부
6. reorder 후 `display_order`는 0..n-1 연속·유일
7. 소프트 삭제 메뉴는 고객 조회에서 제외되나 기존 주문 스냅샷은 유지

### 실기동 검증 — 엔드투엔드 스모크 테스트

백엔드를 실제로 띄운 뒤 로그인→테이블→메뉴→주문→대시보드→상태전이 전 흐름을
검증한다(총액·멱등성 불변식, 인증 경계, SSE 스트림 포함).

```bash
cd backend
DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --workers 1 &
python live_check.py                  # E2E 11개 항목 PASS
```

> Docker 컨테이너 실기동(이미지 빌드 + PostgreSQL 연결)은 Docker 런타임이 있는 환경/CI에서
> `docker compose up`으로 최종 확인한다.

---

## 8. 디렉터리 구조

```
table-order/
├── backend/              FastAPI 애플리케이션 (app/{core,auth,menu,order,realtime,table_session,menu_mgmt}, tests/, alembic/)
├── frontend/             React + Vite (src/customer, src/admin, src/shared)
├── requirements/         사람이 작성한 원본 요구사항·제약 (AI-DLC 입력물)
├── aidlc-docs/           AI-DLC 산출물
│   ├── inception/            🔵 요구사항·스토리·설계·Unit 분해
│   │   ├── plans/                각 Stage 실행 계획
│   │   ├── requirements/         확정 요구사항
│   │   ├── user-stories/         페르소나·스토리·매트릭스
│   │   └── application-design/   컴포넌트·서비스·Unit 정의
│   ├── construction/         🟢 기능/NFR/인프라 설계 + 코드 요약 + 빌드·테스트
│   │   ├── plans/                Stage별 계획
│   │   ├── U0-core ~ U7-frontend/  Unit별 functional-design/ 와 code/ 요약
│   │   ├── nfr-requirements/     비기능 요구·기술 스택 결정
│   │   ├── nfr-design/           설계 패턴·논리 컴포넌트
│   │   ├── infrastructure-design/ 배포 아키텍처
│   │   ├── build-and-test/       빌드·테스트 지침·요약
│   │   └── shared-infrastructure.md
│   ├── aidlc-state.md        진행 상태판(현재 위치·기술 결정·확장 설정)
│   └── audit.md              감사 로그(모든 입력·승인·응답 원문 기록)
├── .aidlc-rule-details/  AI-DLC 규칙 원본(Phase/Stage 정의)
├── CLAUDE.md             AI-DLC 워크플로 최상위 규칙(가장 신뢰도 높은 기준)
├── docker-compose.yml
└── .env.example
```

---

## 9. 현재 상태

- INCEPTION → CONSTRUCTION 전 단계 완료, OPERATIONS는 플레이스홀더(워크플로 종료).
- 백엔드 테스트 17 passed(~85% 커버리지), 프런트엔드 빌드 성공.
- **실기동 검증 완료** — Docker 없이 로컬 네이티브(백엔드 uvicorn+SQLite, 프런트 Vite dev)로 띄워, 브라우저에서 고객 주문 → 관리자 대시보드 실시간 반영 → 테이블 상세/상태전이/메뉴 관리까지 육안 확인(콘솔 에러 0). E2E 스모크 테스트 `backend/live_check.py` 11/11 PASS.
- 유일한 미실행 항목: **Docker 컨테이너 실기동**(런타임 부재로 CI/CD 환경으로 이연).

> **Docker 없이 바로 띄우기(로컬 데모):** 백엔드는 `DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --workers 1` 로, 프런트는 `npm run dev` 로 실행하면 각각 `:8000` / `:5173` 에서 뜬다. 브라우저에서 `http://localhost:5173/admin` → 시드 관리자 계정 로그인 → 테이블 생성/세션 열기 → `http://localhost:5173/customer` 에서 주문하면 관리자 대시보드에 실시간 반영된다. (§6 로컬 개발 참고)

상세 진행 이력은 [`aidlc-docs/aidlc-state.md`](aidlc-docs/aidlc-state.md) 와
[`aidlc-docs/audit.md`](aidlc-docs/audit.md) 참고.
