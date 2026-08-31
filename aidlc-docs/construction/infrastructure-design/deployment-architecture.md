# Deployment Architecture - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - Infrastructure Design
**환경**: 로컬 Docker Compose

---

## 1. 전체 배포 다이어그램

```
                        ┌───────────────────────────────────────┐
                        │        Docker Compose Network          │
                        │            (tableorder-net)            │
                        │                                        │
  고객 태블릿 ─────┐     │   ┌──────────────┐    ┌─────────────┐  │
  (브라우저)       │     │   │  frontend    │    │   backend   │  │
                   ├─────┼──▶│  React SPA   │    │  FastAPI    │  │
  관리자 PC ───────┘     │   │  (vite/nginx)│    │  uvicorn    │  │
  (브라우저)             │   │  :5173/:80   │    │  workers=1  │  │
                        │   └──────┬───────┘    │  :8000      │  │
                        │          │  REST/SSE  │             │  │
                        │          └───────────▶│  ┌────────┐ │  │
                        │                       │  │Event   │ │  │
                        │                       │  │Broker  │ │  │
                        │                       │  │(memory)│ │  │
                        │                       │  └────────┘ │  │
                        │                       └──────┬──────┘  │
                        │                              │ psycopg │
                        │                       ┌──────▼──────┐  │
                        │                       │     db      │  │
                        │                       │ postgres:16 │  │
                        │                       │  :5432      │  │
                        │                       └──────┬──────┘  │
                        │                              │         │
                        │                        [volume: pgdata]│
                        └───────────────────────────────────────┘
```

---

## 2. docker-compose 서비스 정의 (계획)

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      retries: 10

  backend:
    build: ./backend
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: ${DATABASE_URL}
      JWT_SECRET: ${JWT_SECRET}
      JWT_EXP_HOURS: ${JWT_EXP_HOURS}
      CORS_ORIGINS: ${CORS_ORIGINS}
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    depends_on: [backend]
    ports: ["5173:5173"]   # dev; prod는 nginx:80

volumes:
  pgdata:
```
> 위는 설계 계획이며, 실제 파일은 Code Generation 단계에서 생성.

---

## 3. 기동 시퀀스

```
1. docker compose up
2. db 컨테이너 기동 → pg_isready 헬스체크 통과
3. backend 기동 → alembic upgrade head (스키마 생성/갱신)
4. (선택) 시드 데이터 삽입
5. uvicorn 시작 (workers=1) → /health 200
6. frontend 기동 → backend REST/SSE 연결
```

---

## 4. 프로젝트 디렉터리 구조 (계획)

```
table-order/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI 앱 + 라우터 등록 + CORS
│  │  ├─ core/                   # U0: config, db, security(guard), event_broker
│  │  ├─ auth/                   # U1
│  │  ├─ menu/                   # U2
│  │  ├─ order/                  # U3
│  │  ├─ realtime/               # U4 (SSE 엔드포인트, dashboard)
│  │  ├─ table_session/          # U5
│  │  └─ menu_mgmt/              # U6
│  ├─ alembic/                   # 마이그레이션
│  ├─ tests/                     # pytest + hypothesis(PBT)
│  ├─ Dockerfile
│  └─ requirements.txt / pyproject.toml
├─ frontend/                     # U7
│  ├─ src/
│  │  ├─ customer/               # 고객 태블릿 화면
│  │  ├─ admin/                  # 관리자 대시보드
│  │  ├─ shared/                 # RetryClient, SSEClient, CartStore, api
│  │  └─ main.tsx / App.tsx
│  ├─ Dockerfile
│  └─ package.json / vite.config.ts
├─ docker-compose.yml
├─ .env(.example)
└─ README.md
```

> **주의**: 애플리케이션 코드는 워크스페이스 루트(`backend/`, `frontend/`)에 생성. `aidlc-docs/`에는 절대 생성하지 않음.

---

## 5. 확장 경로 (향후, 범위 밖)

| 시나리오 | 필요 변경 |
|---------|----------|
| 다중 인스턴스 SSE | 인메모리 EventBroker → Redis Pub/Sub, 로드밸런서(sticky 불필요) |
| 클라우드 배포 | ECS/Fargate 또는 K8s, 매니지드 PostgreSQL(RDS), 시크릿 매니저 |
| 관측성 | Prometheus/Grafana, 구조적 로그 수집기 |

---

**상태**: ✅ 완료
