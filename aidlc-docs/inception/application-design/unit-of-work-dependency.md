# Unit of Work Dependency - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Units Generation

---

## 1. 의존성 매트릭스

행(의존하는 쪽) → 열(의존 대상). ✅ = 의존.

| ↓Unit \ 대상→ | U0 Core | U1 Auth | U2 Menu | U3 Order | U4 Realtime | U5 Table | U6 MenuMgmt | U7 Frontend |
|---|---|---|---|---|---|---|---|---|
| **U0 Core** | — | | | | | | | |
| **U1 Auth** | ✅ | — | | | | | | |
| **U2 Menu** | ✅ | ✅¹ | — | | | | | |
| **U3 Order** | ✅ | ✅¹ | ✅² | — | ✅³ | | | |
| **U4 Realtime** | ✅ | ✅¹ | | ✅⁴ | — | | | |
| **U5 Table** | ✅ | ✅¹ | | ✅⁴ | ✅³ | — | | |
| **U6 MenuMgmt** | ✅ | ✅¹ | | | | | — | |
| **U7 Frontend** | | | | | | | | — |

**주석**:
- ¹ Auth 가드(U1/U0) 의존: 요청 인증. 실제 가드 구현은 U0(core.security), 토큰 로직은 U1.
- ² Order 생성 시 메뉴 가격/유효성 참조(U2 또는 core.models의 Menu).
- ³ 상태 변경/주문 생성/세션 종료 시 **EventBroker(U0)** 통해 이벤트 발행 → U4가 SSE로 전달. (직접 Unit 호출이 아닌 이벤트 경유, 느슨한 결합)
- ⁴ U4/U5는 Order 데이터(모델/Repository, U0+U3 영역)에 접근.

U7(Frontend)는 백엔드 Unit에 **런타임 REST/SSE**로만 의존(코드 의존 아님) → 매트릭스에서 코드 의존은 없음.

---

## 2. 의존 계층 (빌드/개발 순서)

```
Level 0:  U0 Core (기반: DB, 모델, 가드, EventBroker)
             │
Level 1:  U1 Auth
             │
Level 2:  U2 Menu ── U3 Order
                        │
Level 3:  U4 Realtime & Dashboard  (Order/EventBroker 의존)
             │
Level 4:  U5 Table & Session  (Order 이력 이동, EventBroker)
             │
Level 5:  U6 Menu Management
             
병렬(런타임 연동): U7 Frontend  (백엔드 API 준비되는 대로 통합)
```

- **순환 없음**: 실시간 연동은 EventBroker(U0) 경유이므로 U3↔U4 직접 순환이 발생하지 않음.
- U7은 백엔드와 코드 결합이 없어 병렬 개발 가능(계약=OpenAPI/SSE 스펙 기준).

---

## 3. 통신 패턴 (Unit 간)

| 관계 | 방식 | 비고 |
|------|------|------|
| 도메인 Unit → U0 Core | 인프로세스 함수 호출 (import) | 모델/가드/DB/EventBroker |
| 상태변경 Unit → U4 (실시간) | EventBroker pub/sub (인메모리) | OrderCreated/StatusChanged/Deleted/SessionEnded |
| U7 Frontend → 백엔드 | REST/HTTP + SSE | 런타임, 계약 기반 |
| Unit 간 도메인 로직 | 직접 호출 없음 | 결합 최소화 (이벤트 또는 core 경유) |

---

## 4. 공유 리소스 (U0 Core 집중)

| 리소스 | 사용 Unit |
|--------|----------|
| ORM 모델(9 엔티티) | U1~U6 전부 |
| DB 세션/UoW(트랜잭션) | U3, U4, U5, U6 (쓰기) |
| AuthGuard | U2~U6 전부 |
| EventBroker | U3, U4, U5 |
| 공용 Validator/Schemas | U1~U6 |

→ 공유 요소를 U0에 모아 중복 제거 및 정합성 확보.

---

## 5. 검증

| 항목 | 상태 |
|------|------|
| 의존성 그래프 비순환(DAG)? | ✅ |
| 공유 리소스 단일 소유(U0)? | ✅ |
| 빌드 순서 정의됨? | ✅ (Level 0→5) |
| 프론트 병렬 개발 가능? | ✅ (계약 기반) |

---

**작성일**: 2026-08-31
**상태**: 검토 대기
