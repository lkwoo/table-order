# Business Logic Model - U3 Order (고객 주문)

**작성일**: 2026-08-31 | **Unit**: U3 Order | **스토리**: C10(생성), C11(조회), C12(격리)

---

## 워크플로우 1: 주문 생성 (C10)
```
입력: TableSessionContext(session_id, table_id, store_id),
      items: [{ menu_id, quantity }],
      idempotency_key (클라이언트 생성 UUID)
1. 멱등성 검사: 동일 idempotency_key 주문 존재?
     존재 → 기존 주문 반환(중복 생성 방지, Q6)
2. 세션 유효성: session active & not expired (아니면 401)
3. 서버측 재검증(Q5):
     각 menu_id → Menu 조회(is_active, store_id 일치)
       비활성/없음 → 422 (해당 항목 오류)
     unit_price = 서버의 Menu.price  (클라이언트 값 무시)
     subtotal = unit_price × quantity  (1≤quantity≤99)
4. order_number = 매장 스코프 다음 일련번호 (Q2, 원자적 증가)
5. total_amount = Σ subtotal
6. [TX] Order 저장(status=대기중, session_id 귀속) + OrderItem 스냅샷 저장(menu_name, unit_price)
7. [커밋 후] EventBroker.publish(OrderCreated{store_id, table_id, session_id, order_id})
8. 반환: { order_number, total_amount, status, created_at }
성능: <1초.
```

## 워크플로우 2: 현재 세션 주문 조회 (C11, C12)
```
입력: TableSessionContext(session_id)
1. OrderRepository.list_by_session(session_id)  ← 격리 키 강제(Q4)
2. 시간 역순 정렬
3. 각 주문: order_number, created_at, items(menu_name×qty), total_amount, status
4. 반환 (빈 세션이면 빈 목록)
```
- 이전 세션 주문은 session_id 불일치로 자동 제외(C12).
- 실시간 상태 업데이트는 U4의 SSE(`/sse/orders`)로 수신.

## 워크플로우 3: 장바구니 (C6~C9, 클라이언트)
- 서버 미개입. localStorage에 유지. 최종 확인(C9) 후 워크플로우 1 호출.
- 주문 성공 시 클라이언트가 장바구니 clear + 메뉴 화면 리다이렉트(5초 후).

---

## 데이터 흐름
- 입력 items → 서버 재계산 → Order/OrderItem 저장 → OrderCreated 이벤트.
- 지속성: Order, OrderItem (U0).

## 통합 지점
- U0: OrderRepository, MenuRepository(가격 검증), EventBroker, AuthGuard(세션).
- U4: OrderCreated 이벤트 소비(대시보드/고객 SSE).

## 오류 시나리오
| 상황 | 처리 |
|------|------|
| 중복 idempotency_key | 기존 주문 반환(재시도 안전) |
| 메뉴 비활성/삭제됨 | 422, 주문 거부, 장바구니 유지 |
| 세션 만료 | 401, 재로그인 |
| 네트워크 오류 | 클라이언트 3초 간격 ×3 재시도(동일 멱등키), 최종 실패 시 오류+장바구니 유지 |
| 수량 범위 밖 | 422 |
