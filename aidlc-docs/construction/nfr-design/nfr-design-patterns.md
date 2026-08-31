# NFR Design Patterns - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - NFR Design
**범위**: 프로젝트 레벨 (모놀리스). NFR Requirements를 설계 패턴으로 구체화.

---

## 1. 복원력 패턴 (Resilience)

### 1.1 클라이언트 재시도 (R1/R2)
- **패턴**: Retry with backoff + Idempotency
- **적용**: 프론트엔드 `fetch` 래퍼가 네트워크 오류/5xx에 대해 지수 백오프(예: 300ms→600ms→1200ms) 최대 3회 재시도.
- **주문 생성**: 요청 본문에 클라이언트 생성 `idempotency_key`(UUID) 포함. 서버는 동일 키 재요청 시 기존 주문을 반환(중복 생성 금지).
- **실패 처리**: 재시도 소진 시 사용자에 에러 표시, 장바구니 유지(§3.1.4).

### 1.2 SSE 재연결 (R5)
- **패턴**: Auto-reconnect + State resync (full snapshot)
- **적용**: `EventSource`는 브라우저 기본 자동 재연결. 재연결 이벤트 감지 시 REST로 전체 스냅샷(대시보드/주문내역) 재조회하여 last-write-wins 갱신. 놓친 개별 이벤트 재생하지 않음(FD Q9).

### 1.3 트랜잭션 원자성 (R3/A5)
- **패턴**: Unit-of-Work / Atomic transaction
- **적용**: 세션 종료(이력 복사 + 현재 주문 삭제 + 총액 리셋), 주문 생성(주문+주문항목)은 단일 DB 트랜잭션. 실패 시 전체 롤백.

### 1.4 범위 밖
- Circuit Breaker, Bulkhead, 서버측 큐잉 — 단일 인스턴스 프로토타입에 불필요.

---

## 2. 성능 패턴 (Performance)

### 2.1 조회 최적화 (P1/P2)
- **인덱스**: `Order(table_session_id)`, `Order(store_id, order_number)`, `Menu(store_id, category_id, display_order)`, `OrderHistory(table_id, created_at)`.
- **N+1 방지**: 주문 조회 시 주문항목 eager-load(joinedload/selectinload).

### 2.2 메뉴 응답 캐싱 (P2)
- **패턴**: In-memory cache with short TTL + explicit invalidation
- **적용**: 메뉴 목록(카테고리 포함)을 인메모리 캐시(store_id 키, TTL 30~60s). 메뉴 CRUD/순서 변경 시 해당 store 캐시 무효화.

### 2.3 실시간 = 폴링 제거 (P3/P4)
- **패턴**: Server push (SSE)
- **적용**: 상태 변경/신규 주문은 EventBroker를 통해 즉시 push. 클라이언트 폴링 없음 → 서버 부하 및 지연 최소화(<2s).

### 2.4 프론트 로딩 (P5)
- 이미지 lazy-load(`loading="lazy"`), 라우트 코드 스플리팅(customer/admin), 메뉴 이미지 외부 URL 직접 사용.

---

## 3. 확장성 패턴 (Scalability)

### 3.1 인메모리 EventBroker (S3)
- **패턴**: Publish/Subscribe (in-process)
- **적용**: 토픽 = `store:{id}:admin`(대시보드), `session:{id}:orders`(고객 주문내역). 구독자별 `asyncio.Queue`로 이벤트 팬아웃. 연결 종료 시 구독 해제.
- **경계**: 단일 인스턴스에서만 유효. 멀티 인스턴스 확장 시 외부 Pub/Sub 필요(향후).

### 3.2 비동기 처리
- FastAPI async 라우트 + 비동기 DB 세션으로 20-30 동시 SSE 연결을 이벤트 루프에서 효율 처리.

---

## 4. 보안 패턴 (Security)

### 4.1 인증/인가 (SEC1-3)
- **패턴**: Token-based auth + Dependency guard
- **관리자**: `POST /auth/login` → bcrypt 검증 → JWT(exp=16h) 발급. 이후 `Authorization: Bearer` + `get_current_admin` 의존성 가드.
- **테이블 세션**: 테이블 비밀번호 검증 → 세션 토큰 발급 → `get_current_session` 가드. 관리자/세션 토큰 스코프 분리.

### 4.2 입력 검증 (SEC4)
- **패턴**: Schema validation at boundary
- 모든 요청 본문/쿼리는 Pydantic 스키마로 검증(가격 ≥ 0, 필수 필드, 문자열 길이 등).

### 4.3 금액/격리 무결성 (SEC6/SEC7)
- 주문 금액은 서버가 Menu 테이블 기준 재계산(클라이언트 값 무시).
- 주문 조회는 항상 현재 `table_session_id`로 필터 → 세션 간 격리.

---

## 5. 관측성 & 유지보수 패턴 (M1-M5)

- **계층 분리**: Router(HTTP) → Service(도메인 로직) → Repository(영속성). 트랜잭션은 Service 경계에서 관리.
- **구조적 로깅**: 요청 ID/주문 ID 포함 로그를 stdout으로. (Docker 로그 수집)
- **OpenAPI**: FastAPI 자동 문서(/docs) — API 계약 가시화.
- **PBT**: Hypothesis로 도메인 불변식 검증(§tech-stack §5).

---

## 6. 패턴 ↔ NFR 매핑

| 패턴 | 대응 NFR |
|------|---------|
| Retry + Idempotency | R1, R2, P1 |
| SSE auto-reconnect + snapshot | R5, A2, A3, P3, P4 |
| Atomic transaction (UoW) | R3, A5, D4 |
| In-memory cache (menu) | P2 |
| In-process Pub/Sub broker | S3, P3, P4 |
| Token auth + guard | SEC1, SEC2, SEC3 |
| Schema validation | SEC4 |
| Server-side recompute / session filter | SEC6, SEC7 |

---

**상태**: ✅ 완료
**다음 단계**: Infrastructure Design
