# Infrastructure Design - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - Infrastructure Design
**범위**: 프로젝트 레벨 (모놀리스). 논리 컴포넌트 → 실제 인프라 매핑.
**환경**: 로컬 Docker Compose (개발/시연). 클라우드 배포는 향후(Operations).

---

## 1. 논리 → 물리 매핑

| 논리 컴포넌트 (NFR Design) | 물리 인프라 | 비고 |
|---------------------------|-----------|------|
| FastAPI 앱 (Router/Service/Repo) | `backend` 컨테이너 (python:3.12-slim + uvicorn, **단일 워커**) | 인메모리 상태 일관성 위해 워커 1 |
| EventBroker (인메모리 Pub/Sub) | backend 컨테이너 프로세스 내 (asyncio) | 외부 인프라 없음 |
| MenuCache / IdempotencyStore | backend 프로세스 메모리 / DB 컬럼 | — |
| Repository / SQLAlchemy | backend → `db` 연결 | psycopg v3 |
| PostgreSQL | `db` 컨테이너 (postgres:16) + named volume | 데이터 영속화 |
| React SPA | 개발: `frontend`(vite dev) / 프로덕션: nginx 정적 서빙 | — |
| AuthGuard / Validator | backend 앱 내 (라이브러리) | 인프라 아님 |

---

## 2. 컨테이너 구성 (Docker Compose)

| 서비스 | 이미지 | 포트 | 의존성 | 볼륨 |
|-------|-------|------|-------|------|
| `db` | postgres:16 | 5432 (내부) | — | `pgdata:/var/lib/postgresql/data` |
| `backend` | 로컬 빌드 (Dockerfile) | 8000 | db (healthy) | 소스 마운트(dev) |
| `frontend` | 로컬 빌드 (Dockerfile) | 5173(dev)/80(prod) | backend | 소스 마운트(dev) |

**기동 순서**: db(healthcheck 통과) → backend(Alembic migrate 후 uvicorn) → frontend.

---

## 3. 컴퓨트

- **Backend**: uvicorn, `--workers 1`. 비동기 이벤트 루프로 20-30 동시 SSE 처리.
  - 근거: 인메모리 EventBroker/캐시는 워커 간 공유 불가 → 단일 워커 필수(멀티 워커 시 SSE 구독 분산 문제).
- **수직 확장**: 필요 시 컨테이너 리소스(cpu/mem) 상향. 수평 확장은 외부 브로커 도입 필요(범위 밖).

---

## 4. 스토리지

- **PostgreSQL 16** 컨테이너, named volume `pgdata`로 데이터 영속.
- **마이그레이션**: Alembic. backend 기동 시 `alembic upgrade head` 후 앱 시작(엔트리포인트 스크립트).
- **시드 데이터**: 개발용 매장/관리자/테이블/샘플 메뉴 시드 스크립트(선택).
- **백업/복구 자동화**: 범위 밖(Operations).

---

## 5. 네트워킹

### 개발 (dev)
```
브라우저 ─▶ frontend(vite:5173) ──REST/SSE──▶ backend(uvicorn:8000) ──▶ db(5432)
                     (CORS 허용: localhost:5173 ↔ :8000)
```

### 프로덕션 (참고 — 향후)
```
브라우저 ─▶ nginx:80
              ├─ / (정적 React 빌드 서빙)
              └─ /api, /sse (리버스 프록시 → backend:8000)   # 단일 오리진, CORS 불필요
              (SSE 위해 proxy_buffering off)
```

- **CORS**: 개발에서만 명시적 허용. 프로덕션은 동일 오리진.
- **SSE 주의**: nginx 프록시 시 `proxy_buffering off`, 타임아웃 충분히 크게.

---

## 6. 모니터링 / 헬스체크

| 항목 | 방식 |
|------|------|
| 로그 | 컨테이너 stdout → `docker compose logs` (구조적 로깅) |
| 헬스체크 | backend `GET /health` (DB 연결 확인), db `pg_isready` |
| 관측성 스택 | Prometheus/Grafana/트레이싱 — 범위 밖(Operations) |

---

## 7. 설정 & 시크릿

`.env` (compose가 주입):

| 변수 | 예시 | 용도 |
|------|------|------|
| `DATABASE_URL` | postgresql+psycopg://app:app@db:5432/tableorder | DB 연결 |
| `JWT_SECRET` | (랜덤 문자열) | JWT 서명 |
| `JWT_EXP_HOURS` | 16 | 관리자 세션 만료 |
| `POSTGRES_USER/PASSWORD/DB` | app/app/tableorder | db 초기화 |
| `CORS_ORIGINS` | http://localhost:5173 | 개발 CORS |

> 프로토타입: `.env`는 로컬. 프로덕션 시 시크릿 매니저 권장(범위 밖).

---

## 8. 멀티테넌시 / 격리

- 단일 매장(1 Store) 기준 단일 배포. 데이터는 `store_id`로 스코핑(논리 격리).
- 인프라 레벨 멀티테넌시는 범위 밖.

---

**상태**: ✅ 완료
**관련 문서**: `deployment-architecture.md`, `../shared-infrastructure.md`
