# Tech Stack Decisions - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - NFR Requirements
**근거**: requirements §2/§9 + Application Design + NFR Requirements

---

## 1. 백엔드

| 항목 | 선택 | 버전(권장) | 근거 |
|------|------|-----------|------|
| 언어 | Python | 3.12 | requirements §2.1 |
| 웹 프레임워크 | FastAPI | 0.11x | 비동기, SSE(StreamingResponse) 지원, OpenAPI 자동화 |
| ASGI 서버 | Uvicorn | 최신 | FastAPI 표준 |
| ORM | SQLAlchemy | 2.0 | 성숙한 ORM, 트랜잭션 제어 (R3/A5) |
| 마이그레이션 | Alembic | 최신 | 스키마 버전 관리 |
| 검증 | Pydantic | v2 | 입력 검증(SEC4), 스키마/설정 |
| 인증 | python-jose (JWT) + passlib[bcrypt] | 최신 | SEC1/SEC2 |
| 실시간 | SSE (FastAPI StreamingResponse + 인메모리 EventBroker) | — | Application Design Q4, S3 |

## 2. 프론트엔드

| 항목 | 선택 | 버전(권장) | 근거 |
|------|------|-----------|------|
| 프레임워크 | React | 18 | requirements §2.2 |
| 빌드 도구 | Vite | 최신 | 빠른 개발 서버, 경량 |
| 언어 | TypeScript | 5.x | 타입 안정성 (프로토타입이지만 권장) |
| 라우팅 | React Router | 6 | /customer, /admin 경로 분리 (App Design Q2) |
| 상태 관리 | Context + hooks | — | 경량 (FD Q8), 장바구니는 localStorage 동기화 |
| HTTP | fetch + 재시도 래퍼 | — | idempotency-key 재시도 (R1/R2) |
| SSE | EventSource API | — | 브라우저 네이티브, 자동 재연결 + 스냅샷 재조회 (R5) |
| 스타일 | CSS Modules (or 경량 UI) | — | 프로토타입 단순성 |

## 3. 데이터베이스

| 항목 | 선택 | 버전(권장) | 근거 |
|------|------|-----------|------|
| RDBMS | PostgreSQL | 16 | ACID 트랜잭션(A5/R3), 안정성 (requirements §2.1) |
| 드라이버 | psycopg (v3) | 최신 | SQLAlchemy 2.0 호환 |

## 4. 개발/실행 환경

| 항목 | 선택 | 근거 |
|------|------|------|
| 컨테이너 | Docker Compose | requirements §2.3 |
| 서비스 구성 | `db`(postgres) + `backend`(fastapi/uvicorn) + `frontend`(vite dev / nginx) | 모놀리스, 로컬 개발 |
| 환경변수 | `.env` (DB URL, JWT_SECRET, JWT_EXP=16h) | 설정 분리 |

## 5. 테스트

| 항목 | 선택 | 근거 |
|------|------|------|
| 단위/통합 | pytest | Python 표준 |
| Property-Based | **Hypothesis** | Extension 활성 — 주문/결제 정합성 불변식 (M4) |
| 프론트 | Vitest + React Testing Library | Vite 생태계 |

### PBT 대상 불변식 (Functional Design에서 도출)
- 주문 총액 = Σ(단가 × 수량) — 서버 재계산 일치
- idempotency-key 재시도 시 주문 1건만 생성
- 세션 종료 시 이관 합계 = 종료 전 현재 주문 합계 (합 보존)
- 세션 격리: 세션 A 조회에 세션 B 주문 미포함
- 메뉴 소프트 삭제 후에도 기존 주문/이력 스냅샷 보존

## 6. 명시적 비선택 (Out of Scope)

| 항목 | 사유 |
|------|------|
| WebSocket | 단방향 push엔 SSE로 충분 (requirements §9) |
| Redis / 외부 메시지 브로커 | 단일 인스턴스 인메모리 EventBroker로 충분 (S3) |
| Redux 등 전역 상태 라이브러리 | Context+hooks로 충분 (FD Q8) |
| 파일 업로드/이미지 스토리지 | 외부 URL만 사용 (범위 밖) |
| 실제 결제 게이트웨이 | 범위 밖 (constraints) |
| K8s / 클라우드 매니지드 서비스 | 프로토타입 — Docker Compose 로컬 (배포는 향후) |

---

**상태**: ✅ 완료
**다음 단계**: NFR Design
