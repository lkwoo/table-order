# U0-core — 코드 요약

공유 기반(Foundation) 레이어. 모든 유닛이 의존한다.

## 생성 파일 (`backend/app/core/`)
- `config.py` — Pydantic `Settings` 싱글턴(`settings`). DATABASE_URL, JWT, CORS, 가격 1,000~100,000, 수량 1~99, 이력 보관 90일.
- `db.py` — SQLAlchemy `engine`, `SessionLocal`, `get_db()` 의존성, `unit_of_work()` 컨텍스트매니저(성공 시 commit, 예외 시 rollback).
- `types.py` — `GUID` TypeDecorator: PostgreSQL 은 `UUID`, 그 외(SQLite 테스트)는 `CHAR(32)`.
- `models.py` — `Base`(DeclarativeBase), `OrderStatus`(대기중/준비중/완료), `SessionStatus`(active/ended), `ALLOWED_TRANSITIONS`(단방향), 11개 모델(Store, Admin, Table, TableSession, MenuCategory, Menu, Order, OrderItem, OrderHistory, OrderHistoryItem).
- `errors.py` — HTTP 예외 헬퍼(401/403/404/409/422).
- `security.py` — bcrypt 해시/검증, 관리자 JWT(16h), `AdminContext`/`SessionContext` 및 의존성.
- `event_broker.py` — 인프로세스 Pub/Sub `EventBroker`(asyncio.Queue, maxsize=100), 토픽 헬퍼, `broker` 싱글턴.
- `logging.py` — stdout 로깅 설정.

## 핵심 규칙
- 트랜잭션 경계는 서비스의 `unit_of_work()` 에서만. 이벤트는 커밋 이후 발행.
- 상태 전이는 `ALLOWED_TRANSITIONS` 로 강제(완료 → 이전 불가).
- DB 이식성(GUID)으로 SQLite 기반 속성 테스트 가능.
