# Business Logic Model - U5 Table & Session

**작성일**: 2026-08-31 | **Unit**: U5 | **스토리**: A5(초기설정), A7(세션종료), A8(이력조회)

---

## 워크플로우 1: 테이블 초기 설정 (A5)
```
입력: table_number, password, AdminContext(store_id)
1. 중복 검사: (store_id, table_number) 존재? → 409
2. password 검증(4~10자리), bcrypt 해싱
3. [TX] Table 생성 + active TableSession 생성(token, expires=now+16h)
4. 반환: { table_id, table_number, session created }
```

## 워크플로우 2: 테이블 세션 종료 (A7) — 원자적 이력 이동
```
입력: table_id, AdminContext
1. active 세션 및 현재 주문 목록 조회
2. [단일 TX]:
     a. 각 Order → OrderHistory 스냅샷 삽입(order_number, final_status, total, ordered_at, completed_at)
        각 OrderItem → OrderHistoryItem 스냅샷(menu_name, unit_price, quantity, subtotal)  (Q3)
     b. 현재 Order/OrderItem 삭제 (테이블 현재 주문 리셋, 총액 0)
     c. 기존 TableSession.status = ended, ended_at = now
     d. 새 TableSession 생성(status=active, 새 id/token, expires=now+16h)
   ── 커밋 (전부 성공 또는 전부 롤백)
3. [커밋 후] EventBroker.publish(SessionEnded{table_id})
     → 대시보드 카드 총액 0으로 갱신
4. 반환: 성공 피드백
결과: 새 고객이 즉시 로그인 가능(새 세션).
```

## 워크플로우 3: 과거 이력 조회 (A8)
```
입력: table_id, date_filter(모든/오늘/어제/범위), AdminContext
1. OrderHistoryRepository.list_by_table(table_id, date_range)
2. 3개월 이내 데이터, 시간 역순 정렬
3. 각 이력: order_number, ordered_at, items, total, completed_at
4. 결과 없으면 빈 목록(프론트 "주문 없음" 표시)
```

---

## 통합 지점
- U0: TableRepository, TableSessionRepository, OrderRepository, OrderHistoryRepository, EventBroker.
- 세션 종료 후 C12(고객 격리)와 연결: 새 세션 id로 이전 주문 자동 분리.

## 오류 시나리오
| 상황 | 처리 |
|------|------|
| 테이블 번호 중복(A5) | 409 |
| 세션 종료 중 오류 | 전체 롤백, 오류 응답, "다시 시도" |
| 이력 없는 기간(A8) | 빈 목록 |
