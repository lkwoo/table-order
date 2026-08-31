# Services - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Application Design
**패턴**: 도메인별 서비스 + 레이어드(Service가 트랜잭션 경계 소유) + 인메모리 이벤트 발행

---

## 서비스 목록 및 책임

| 서비스 | 도메인 | 핵심 책임 | 트랜잭션 | 이벤트 발행 |
|--------|--------|----------|---------|-----------|
| **AuthService** | 인증 | 관리자 JWT / 고객 세션 토큰 발급·검증, bcrypt | 조회성(무상태) | - |
| **MenuService** | 메뉴(조회) | 카테고리별·정렬 메뉴 조회 | 읽기 | - |
| **MenuManagementService** | 메뉴(관리) | 메뉴 CRUD, 순서 조정, 검증 | 쓰기 | - (고객은 다음 조회 시 반영) |
| **OrderService** | 주문(고객) | 주문 생성, 현재 세션 주문 조회 | 쓰기(생성) | `OrderCreated` |
| **OrderAdminService** | 주문(관리) | 상태 변경, 삭제, 총액 재계산 | 쓰기 | `OrderStatusChanged`, `OrderDeleted` |
| **TableSessionService** | 테이블/세션 | 테이블 설정, 세션 종료(이력 이동), 과거 이력 조회 | 쓰기(원자적) | `SessionEnded` |
| **DashboardService** | 대시보드 | 테이블 카드 데이터 집계 | 읽기 | - |
| **EventBroker** | 실시간 | 인메모리 pub/sub, SSE 구독자 관리 | - | (전달자) |

---

## 오케스트레이션 시나리오

### 시나리오 1: 고객 주문 생성 (C10 → A2)

```
CustomerApp
  └─ POST /orders  (X-Session-Token)
       └─ get_current_table_session (AuthGuard)
            └─ OrderService.create_order(session_ctx, items)
                 ├─ [TX] OrderRepository.add(order + items)   # 커밋
                 └─ EventBroker.publish(OrderCreated{store, table, session})
                      ├─▶ subscribe_dashboard(store)  → 관리자 대시보드 카드 갱신 (A2)
                      └─ (해당 세션 구독자 없으면 무시)
```
성능 목표: 주문 생성 < 1초, 대시보드 반영 < 2초.

### 시나리오 2: 관리자 상태 변경 (A4 → C11)

```
AdminApp
  └─ PATCH /admin/orders/{id}/status  (JWT)
       └─ get_current_admin (AuthGuard)
            └─ OrderAdminService.update_order_status(order_id, new_status)
                 ├─ [TX] 상태 전이 검증 + 저장 + 변경 로그
                 └─ EventBroker.publish(OrderStatusChanged{session, order})
                      ├─▶ subscribe_session(session) → 고객 주문내역 실시간 갱신 (C11, <2초)
                      └─▶ subscribe_dashboard(store)  → 대시보드 카드 갱신
```

### 시나리오 3: 테이블 세션 종료 (A7) — 원자적 트랜잭션

```
AdminApp
  └─ POST /admin/tables/{id}/end-session  (JWT)
       └─ TableSessionService.end_session(table_id)
            └─ [단일 TX]
                 1. OrderHistoryRepository.bulk_insert(현재 주문들)
                 2. OrderRepository.delete_by_table(table_id)   (현재 주문 리셋)
                 3. TableSessionRepository.create_session(table_id, now+16h)  (새 session_id)
               ── 커밋 (전부 성공 또는 전부 롤백)
            └─ EventBroker.publish(SessionEnded{table})
                 └─▶ subscribe_dashboard(store) → 카드 총액 0으로 갱신
```
실패 시 전체 롤백 → 데이터 정합성 보장 (요구사항 4.4).

### 시나리오 4: 주문 삭제 (A6)

```
AdminApp → DELETE /admin/orders/{id}
  └─ OrderAdminService.delete_order(order_id)
       ├─ [TX] 주문 삭제 + 삭제 로그
       ├─ 테이블 총액 재계산 (OrderRepository.sum_total_by_table)
       └─ EventBroker.publish(OrderDeleted)
            ├─▶ 대시보드 카드 갱신
            └─▶ 고객 주문내역에서 제거 (SSE)
```

### 시나리오 5: 메뉴 순서 조정 (A13 → C3)

```
AdminApp → PATCH /admin/menus/reorder
  └─ MenuManagementService.reorder_menus(category, ordered_ids)
       └─ [TX] display_order 일괄 갱신 (실패 시 롤백 → 기존 순서 유지)
   (고객 C3은 다음 메뉴 조회 시 새 순서 반영 — 실시간 push 불필요)
```

---

## SSE 스트림 서비스 (Q5: 대상별 엔드포인트 분리)

| 엔드포인트 | 대상 | 인증 | 구독 이벤트 |
|-----------|------|------|-----------|
| `GET /sse/orders?session_id=` | 고객 | 세션 토큰 | `OrderStatusChanged`, `OrderDeleted` (자기 세션만) |
| `GET /sse/dashboard` | 관리자 | JWT | `OrderCreated`, `OrderStatusChanged`, `OrderDeleted`, `SessionEnded` (매장 전체) |

- **EventBroker**는 단일 서버 인스턴스의 인메모리 구조(asyncio Queue 기반 구독자 레지스트리).
- 연결 종료/타임아웃 시 `unsubscribe`로 정리.
- 오프라인 후 재연결(A2): 클라이언트가 재연결하면 대시보드 데이터를 REST로 1회 재조회하여 갭 보정(Q9).

---

## 트랜잭션·정합성 정책

- **쓰기 서비스**가 트랜잭션 경계를 소유 (Unit of Work). Repository는 트랜잭션을 열지 않음.
- **이벤트 발행은 커밋 이후**에만 수행 (커밋 실패 시 이벤트 없음).
- **세션 격리**(C12): OrderService 조회는 항상 현재 `session_id`로 필터 — 서비스 레벨에서 강제.
- **참조 무결성**(A12): 메뉴 삭제 시 과거 이력의 메뉴명은 스냅샷으로 보존(이력에 메뉴명 텍스트 저장).

---

## 서비스-스토리 커버리지

| 서비스 | 커버 스토리 |
|--------|-----------|
| AuthService | A1, C1, C2 |
| MenuService | C3, C4 |
| MenuManagementService | A9, A10, A11, A12, A13 |
| OrderService | C6~C10(생성), C11, C12 |
| OrderAdminService | A3, A4, A6 |
| TableSessionService | A5, A7, A8 |
| DashboardService | A2 |
| EventBroker | A2, A4, A6, A7, C11 |

> 장바구니(C6~C9)는 클라이언트 localStorage 중심이며, 서버는 주문 생성 시점(C10)에만 관여.

---

**작성일**: 2026-08-31
**상태**: 검토 대기
**다음 문서**: `component-dependency.md`
