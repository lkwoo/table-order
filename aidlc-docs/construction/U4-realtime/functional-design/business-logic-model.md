# Business Logic Model - U4 Realtime & Dashboard

**작성일**: 2026-08-31 | **Unit**: U4 | **스토리**: A2(대시보드), A3(상세), A4(상태변경), A6(삭제)

---

## 워크플로우 1: 대시보드 데이터 (A2)
```
입력: AdminContext(store_id)
1. store의 Table 목록 조회
2. 각 table의 active 세션 현재 주문 집계:
     total_amount = Σ 미종료 주문 금액
     recent_orders = 최신 3개 미리보기(menu 요약)
3. 반환: [{ table_number, total_amount, recent_orders, has_new }]
```
- 초기 로드는 REST, 이후 변화는 `/sse/dashboard` 이벤트로 증분 갱신.

## 워크플로우 2: 테이블 상세 주문 (A3)
```
입력: table_id
1. 해당 table active 세션 주문 전체 조회
2. 각 주문: order_number, created_at, items(명/수량/소계), total, status
3. 반환
```

## 워크플로우 3: 주문 상태 변경 (A4)
```
입력: order_id, new_status, AdminContext
1. Order 조회(store_id 일치)
2. 전이 검증(Q1): 대기중→준비중→완료 단방향만 허용
     역전이/불가 전이 → 409
3. [TX] status 갱신, updated_at 기록, 상태 변경 로그 기록
4. [커밋 후] EventBroker.publish(OrderStatusChanged{session_id, order_id, new_status})
     → /sse/orders(고객): 주문내역 실시간 갱신(<2초)
     → /sse/dashboard(관리자): 카드 갱신
5. 반환: 갱신된 주문
```

## 워크플로우 4: 주문 삭제 (A6)
```
입력: order_id, AdminContext
1. Order 조회(store_id 일치)
2. [TX] Order + OrderItem 삭제, 삭제 로그 기록
3. 테이블 총액 재계산(집계)
4. [커밋 후] EventBroker.publish(OrderDeleted{session_id, table_id, order_id})
     → 고객 주문내역에서 제거, 대시보드 카드 갱신
5. 반환: { table_total }
```

## 워크플로우 5: SSE 스트림
```
/sse/dashboard (관리자 JWT):
  구독 시작 → EventBroker.subscribe_dashboard(store_id)
  이벤트: OrderCreated/StatusChanged/Deleted/SessionEnded (매장 전체)
  연결 종료 시 unsubscribe

/sse/orders?session_id= (고객 세션 토큰):
  구독 시작 → subscribe_session(session_id)
  이벤트: OrderStatusChanged/OrderDeleted (자기 세션만)

오프라인 재연결(Q9): 클라이언트 재연결 시 대시보드 REST 스냅샷 재조회로 최신화(last-write-wins)
```

---

## 통합 지점
- U0: OrderRepository, EventBroker, AuthGuard. U3: 주문 데이터.
- 신규 주문 강조(has_new): OrderCreated 수신 후 프론트에서 3초 하이라이트.

## 오류 시나리오
| 상황 | 처리 |
|------|------|
| 잘못된 상태 전이 | 409 |
| 이미 삭제된 주문 상태 변경 | 404 |
| SSE 연결 끊김 | 클라이언트 자동 재연결 + 스냅샷 재조회 |
| 상태 변경 서버 오류 | 오류 응답, 프론트 "다시 시도" |
