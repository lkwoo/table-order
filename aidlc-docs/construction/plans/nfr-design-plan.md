# NFR Design Plan - 테이블오더 서비스 (프로젝트 레벨)

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - NFR Design
**범위**: NFR Requirements를 설계 패턴·논리 컴포넌트로 구체화

---

# PART 1: PLANNING - 체크리스트

## Step 1: NFR Requirements 분석 ✅
- [x] nfr-requirements.md / tech-stack-decisions.md 검토

## Step 2: 결정 질문 답변 (PART 2) ✅
- [x] 모든 [Answer]: 태그 작성 (전부 권장)

## Step 3: 산출물 생성 ✅
- [x] `nfr-design/nfr-design-patterns.md`
- [x] `nfr-design/logical-components.md`

---

# PART 2: NFR 설계 결정 질문

## Q1. 복원력 패턴 (Resilience)

네트워크 오류·SSE 단절 대응 패턴은?

- **A) 클라이언트 지수 백오프 재시도(최대 3회) + idempotency-key + SSE 자동 재연결 후 스냅샷 재조회** ⭐권장
  - Circuit Breaker/Bulkhead는 단일 인스턴스 프로토타입엔 과함
- **B) 서버측 Circuit Breaker + 큐잉 도입**

[Answer]: A

---

## Q2. 성능 패턴 (Performance)

성능 목표 달성 패턴은?

- **A) DB 인덱스(세션/테이블/카테고리) + 메뉴 조회 응답 캐싱(인메모리, 짧은 TTL) + 이미지 lazy-load + SSE로 폴링 제거** ⭐권장
- **B) 별도 캐시 서버(Redis) 도입**

[Answer]: A

---

## Q3. 확장성 패턴 (Scalability)

SSE 팬아웃 및 부하 처리는?

- **A) 단일 인스턴스 인메모리 EventBroker(토픽: store/table 별 구독), 비동기 큐로 이벤트 팬아웃** ⭐권장
  - 20-30 동시 연결에 충분. 멀티 인스턴스는 범위 밖
- **B) 외부 Pub/Sub(Redis) 기반 팬아웃**

[Answer]: A

---

## Q4. 보안 패턴 (Security)

인증/인가 구현 패턴은?

- **A) JWT Bearer(관리자) + 세션 토큰(테이블), FastAPI Dependency guard로 라우트 보호, bcrypt 해싱, Pydantic 입력 검증** ⭐권장
- **B) 세션 서버(서버측 세션 저장소) 도입**

[Answer]: A

---

## Q5. 논리 컴포넌트 구성 (Logical Components)

인프라성 논리 컴포넌트 범위는?

- **A) EventBroker(인메모리) + AuthGuard + Repository(트랜잭션 경계) + IdempotencyStore(주문 키) + 경량 인메모리 캐시** ⭐권장
  - 외부 큐/캐시/서킷브레이커 없이 애플리케이션 내부 컴포넌트로 구현
- **B) 외부 인프라 컴포넌트(Redis/큐) 도입**

[Answer]: A

---

**상태**: 답변 완료 (전부 권장) → 산출물 생성 완료
