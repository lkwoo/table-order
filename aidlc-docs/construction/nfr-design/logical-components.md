# Logical Components (NFR) - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - NFR Design
**범위**: NFR을 실현하는 논리 컴포넌트 (모두 애플리케이션 내부 — 외부 인프라 없음)

---

## 1. 논리 컴포넌트 목록

| 컴포넌트 | 위치(Unit) | 책임 | 실현 NFR |
|---------|-----------|------|---------|
| **EventBroker** | U0 Core | 인메모리 Pub/Sub. 토픽별 구독자 asyncio.Queue 관리, publish/subscribe/unsubscribe | S3, P3, P4, R5 |
| **AuthGuard (Dependencies)** | U0/U1 | JWT 검증(관리자), 세션 토큰 검증(테이블), 라우트 인가 | SEC1-3, SEC7 |
| **Repository Layer** | 각 도메인 Unit | DB 접근 캡슐화 + 트랜잭션 경계(Unit-of-Work) | R3, A5, D4 |
| **IdempotencyStore** | U3 Order | idempotency_key → order_id 매핑 저장(주문 테이블 컬럼 or 보조 테이블) | R2 |
| **MenuCache** | U2 Menu | store 단위 메뉴 목록 인메모리 캐시(TTL + 무효화) | P2 |
| **RetryClient (FE)** | U7 Frontend | fetch 래퍼: 백오프 재시도 + idempotency-key 주입 | R1, R2, R4 |
| **SSEClient (FE)** | U7 Frontend | EventSource 관리: 자동 재연결 + 재연결 시 스냅샷 재조회 | R5, A2, A3 |
| **CartStore (FE)** | U7 Frontend | localStorage 동기화 장바구니 상태 | A4 |
| **Validator (Pydantic schemas)** | 전체 | 경계 입력 검증 | SEC4 |

---

## 2. EventBroker 상세 (핵심 컴포넌트)

```
EventBroker (singleton, in-process)
├─ subscribe(topic) -> asyncio.Queue         # SSE 연결마다 큐 생성
├─ unsubscribe(topic, queue)                 # 연결 종료 시 정리
└─ publish(topic, event)                     # 모든 구독 큐에 fan-out

토픽 규칙:
  - "store:{store_id}:dashboard"   # 관리자: 신규 주문/상태 변경
  - "session:{session_id}:orders"  # 고객: 자기 세션 주문 상태 변경

이벤트 타입:
  - order.created        (→ dashboard)
  - order.status_changed (→ dashboard + session)
  - order.deleted        (→ dashboard + session)
  - session.ended        (→ dashboard)
```

**흐름 예시 (주문 상태 변경 → 고객·관리자 반영, <2s)**:
```
Admin PATCH /orders/{id}/status
  → OrderService.update_status() [tx]
  → EventBroker.publish("store:1:dashboard", order.status_changed)
  → EventBroker.publish("session:abc:orders", order.status_changed)
  → 구독 중인 SSE 연결들의 Queue로 즉시 전달
  → 클라이언트 EventSource onmessage → UI 갱신
```

---

## 3. 트랜잭션 경계 (Unit-of-Work)

| 연산 | 트랜잭션 범위 | 이벤트 발행 시점 |
|------|-------------|----------------|
| 주문 생성 | Order + OrderItem insert + 멱등키 기록 | 커밋 성공 후 order.created |
| 상태 변경 | Order.status update | 커밋 성공 후 order.status_changed |
| 주문 삭제 | Order/OrderItem delete + 총액 재계산 | 커밋 성공 후 order.deleted |
| 세션 종료 | OrderHistory insert(스냅샷) + Order 삭제 + 새 세션 생성 | 커밋 성공 후 session.ended |

> 원칙: **이벤트는 트랜잭션 커밋 성공 이후에만 발행**(부분 상태 노출 방지).

---

## 4. 배치도 (논리)

```
┌─────────────────────────── FastAPI (단일 프로세스) ───────────────────────────┐
│                                                                               │
│  Routers ──> Services ──> Repositories ──> [SQLAlchemy] ──> PostgreSQL        │
│    │            │                                                             │
│    │            └──> EventBroker (in-memory Pub/Sub)                          │
│    │                    │                                                     │
│    ├─ AuthGuard (JWT / session token dependency)                             │
│    ├─ MenuCache (in-memory, TTL)                                             │
│    └─ IdempotencyStore (DB)                                                   │
│                                                                               │
│  SSE endpoints ◀── subscribe ── EventBroker                                   │
└───────────────────────────────────────────────────────────────────────────┘
        ▲  REST + SSE
        │
┌───────┴───────────────────────────┐
│ React SPA (Vite)                   │
│  RetryClient / SSEClient / CartStore │
│  /customer  |  /admin              │
└────────────────────────────────────┘
```

---

## 5. 외부 인프라 컴포넌트 (명시적 미사용)

| 컴포넌트 | 결정 | 사유 |
|---------|------|------|
| Redis / 외부 캐시 | ❌ | 인메모리 캐시로 충분 |
| 메시지 큐 (SQS/Kafka) | ❌ | 인메모리 EventBroker로 충분 |
| API Gateway / 로드밸런서 | ❌ | 단일 인스턴스 (프로덕션 시 리버스 프록시만) |
| Circuit Breaker 라이브러리 | ❌ | 클라이언트 재시도로 충분 |

---

**상태**: ✅ 완료
**다음 단계**: Infrastructure Design
