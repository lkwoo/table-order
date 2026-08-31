# U3-order — 코드 요약

고객 주문 생성·조회.

## 생성 파일 (`backend/app/order/`)
- `schemas.py` — `OrderCreate`(idempotency_key, items), `OrderItemIn`(수량 1~99 검증), `OrderOut`.
- `repository.py` — `get_by_idempotency_key`, `next_order_number`(현재+이력 최대치+1), `list_by_session`(desc), `get_by_id`.
- `service.py` — `create_order`(R4 idempotency, R1 서버 금액 재계산, R7 메뉴명·단가 스냅샷, R8 커밋 후 이벤트 발행), `list_current_orders`(세션 격리).
- `router.py` — `POST /api/orders`, `GET /api/orders`.

## 규칙 (검증됨)
- R1: `total_amount == Σ(unit_price × quantity)`.
- R4: 동일 idempotency_key 재요청 → 기존 주문 반환(중복 없음).
- 세션 격리: 조회는 요청 세션의 주문만.

## 테스트 (`backend/tests/test_pbt_order.py`)
- 총액 불변식, idempotency(N회 → 1건), 세션 격리 — 모두 Hypothesis PBT.
