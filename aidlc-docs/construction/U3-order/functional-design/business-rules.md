# Business Rules - U3 Order

**작성일**: 2026-08-31 | **Unit**: U3 Order

---

| # | 규칙 |
|---|------|
| R1 | 주문 금액은 **서버가 Menu.price 기준으로 계산** (클라이언트 값 불신, Q5) |
| R2 | 주문은 생성 시점 active TableSession.id에 귀속 (Q4) |
| R3 | 조회는 현재 session_id로만 필터 — 세션 격리 절대 보장 (C12) |
| R4 | idempotency_key 중복 시 신규 생성 없이 기존 주문 반환 (Q6) |
| R5 | order_number는 매장 스코프 단조 증가 정수 (Q2), 세션 종료와 무관하게 연속 |
| R6 | quantity 1~99, 각 subtotal = unit_price × quantity |
| R7 | OrderItem은 주문 시점 menu_name/unit_price 스냅샷 저장(이후 메뉴 변경 무관) |
| R8 | 주문 생성 성공 시에만 OrderCreated 이벤트 발행(커밋 후) |
| R9 | 비활성(is_active=false) 메뉴는 주문 불가 → 422 |

## 상태
- 신규 주문 status = 대기중. 이후 상태 전이는 U4(A4) 소관.

## Property-Based Test 후보
- 임의 items 조합에 대해 `total_amount == Σ(unit_price×quantity)` 불변식
- 동일 idempotency_key로 N회 호출 시 주문 1건만 생성(멱등성)
- 임의 세션 A의 조회 결과에 세션 B의 주문이 절대 포함되지 않음(격리)
- order_number 단조 증가 & 매장 내 유일
