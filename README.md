# 테이블오더 (Table Order)

식당 테이블에서 고객이 직접 메뉴를 주문하고, 관리자가 실시간 대시보드로
주문을 관리하는 웹 서비스. AI-DLC 방법론에 따라 설계·구현되었다.

- 설계 산출물: [`aidlc-docs/`](aidlc-docs/)
- 요구사항: [`requirements/`](requirements/)

## 기술 스택

| 영역 | 스택 |
| --- | --- |
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · PostgreSQL 16 |
| 실시간 | 인프로세스 EventBroker(asyncio) + SSE(Server-Sent Events) |
| Auth | JWT(python-jose) · bcrypt(passlib) |
| Frontend | React 18 · TypeScript · Vite · React Router 6 |
| 테스트 | pytest · Hypothesis(속성 기반 테스트) |
| 배포 | Docker Compose (db · backend · frontend) |

> 백엔드는 인메모리 EventBroker 상태 일관성을 위해 **단일 워커**로 실행한다.

## 아키텍처

계층형 구조: `Router → Service → Repository`. 트랜잭션 경계는 서비스의
Unit-of-Work 에서 관리하며, 이벤트는 **커밋 이후에만** 발행한다.

핵심 도메인 규칙:
- 주문 idempotency-key 로 중복 제출 방지
- 금액은 서버에서 재계산(클라이언트 값 신뢰 안 함)
- 세션 격리: `TableSession.id` 기준으로 주문 분리
- 메뉴는 소프트 삭제, 주문/이력에는 스냅샷(이름·단가) 보존
- 주문 상태 전이는 단방향 (대기중 → 준비중 → 완료)

## 빠른 시작 (Docker Compose)

```bash
cp .env.example .env      # 필요 시 값 수정
docker compose up --build
```

- 프런트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000  (헬스체크: `/health`)

초기 시드 계정(자동 생성):
- 관리자 로그인 — 매장 ID `11111111-1111-1111-1111-111111111111`, 아이디 `admin`, 비밀번호 `admin1234`

## 로컬 개발

### 백엔드

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows (bash: source .venv/Scripts/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --workers 1
```

기본 설정은 `postgresql+psycopg://app:app@db:5432/tableorder` 를 가리킨다.
로컬 PostgreSQL 이나 `DATABASE_URL` 환경 변수로 조정한다.

### 프런트엔드

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, /api 는 localhost:8000 으로 프록시
```

## 테스트

속성 기반 테스트(Hypothesis)로 7개 핵심 불변식을 검증한다.

```bash
cd backend
.venv/Scripts/python -m pytest
```

검증하는 불변식:
1. 주문 총액 = Σ(단가 × 수량)
2. 동일 idempotency-key N회 요청 → 주문 1건
3. 세션 격리 (세션 A 조회에 세션 B 주문 없음)
4. 세션 종료 시 합계 보존 (이력 합계 == 종료 전 합계)
5. `완료` 상태에서 이전 상태로의 전이 항상 거부
6. reorder 후 `display_order` 는 0..n-1 연속·유일
7. 소프트 삭제 메뉴는 고객 조회에서 제외되나 기존 주문 스냅샷은 유지

## 디렉터리 구조

```
table-order/
├── backend/            FastAPI 애플리케이션 (app/, tests/, alembic/)
├── frontend/           React + Vite (src/customer, src/admin, src/shared)
├── aidlc-docs/         AI-DLC 설계 산출물 (inception, construction)
├── requirements/       원본 요구사항
├── docker-compose.yml
└── .env.example
```
