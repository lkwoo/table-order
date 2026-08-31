# Shared Infrastructure - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - Infrastructure Design
**범위**: 8개 Unit이 공유하는 공용 인프라 (모놀리스 단일 배포)

---

## 1. 공유 원칙

테이블오더는 **단일 모놀리스**로 배포되므로, 모든 Unit(U0~U7)은 동일한 런타임/인프라를 공유합니다. Unit은 배포 단위가 아닌 **논리 모듈**입니다.

---

## 2. 공유 인프라 자원

| 자원 | 공유 방식 | 소유 Unit | 사용 Unit |
|------|----------|----------|----------|
| PostgreSQL (`db`) | 단일 DB 인스턴스/스키마 | U0 Core (연결/세션 관리) | 전체 |
| DB 커넥션 풀 | SQLAlchemy 엔진(단일) | U0 Core | 전체 |
| EventBroker (인메모리) | 프로세스 내 싱글턴 | U0 Core | U3(발행), U4(구독/SSE), U5(발행) |
| AuthGuard (의존성) | FastAPI Dependency | U0/U1 | 보호가 필요한 전체 라우트 |
| 설정(.env/Settings) | Pydantic Settings 싱글턴 | U0 Core | 전체 |
| 로깅 | stdout 구조적 로거 | U0 Core | 전체 |
| HTTP 서버(uvicorn) | 단일 프로세스(workers=1) | — | 전체 |

---

## 3. U0 Core/Shared 인프라 책임

`backend/app/core/`:
- `config.py` — 환경변수/설정(DATABASE_URL, JWT_SECRET, JWT_EXP_HOURS, CORS_ORIGINS)
- `db.py` — SQLAlchemy 엔진/세션, 트랜잭션 유틸(Unit-of-Work)
- `security.py` — bcrypt 해싱, JWT 발급/검증, AuthGuard 의존성(get_current_admin / get_current_session)
- `event_broker.py` — 인메모리 Pub/Sub (subscribe/unsubscribe/publish)
- `models_base.py` — SQLAlchemy Base, 공통 믹스인(id, created_at)
- `logging.py` — 구조적 로거 설정

---

## 4. 배포/운영 공유 사항

| 항목 | 내용 |
|------|------|
| 단일 네트워크 | compose `tableorder-net` 내 db/backend/frontend |
| 마이그레이션 | Alembic — 전체 Unit의 테이블을 단일 마이그레이션 체인으로 관리 |
| 헬스체크 | `/health` (전체 앱 단일 엔드포인트) |
| 시크릿 | `.env` 공유 (JWT_SECRET 등) |

---

## 5. 워커 단일화 제약 (중요)

- EventBroker와 MenuCache가 **프로세스 인메모리** 상태이므로 backend는 **단일 워커/단일 인스턴스**로 실행해야 함.
- 멀티 워커/인스턴스가 필요해지면 외부 브로커(Redis Pub/Sub) + 외부 캐시로 이 공유 자원을 대체해야 함(향후, 범위 밖).

---

**상태**: ✅ 완료
