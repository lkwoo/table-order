# U4-realtime — 코드 요약

관리자 실시간 대시보드, 주문 상태 변경/삭제, SSE 스트림.

## 생성 파일 (`backend/app/realtime/`)
- `schemas.py` — `TableCardOut`, `AdminOrderOut`, `StatusUpdate`, `DeleteResult`, `RecentOrderOut`.
- `service.py` — `get_dashboard`(테이블별 active 세션 주문 집계, 총액=합), `get_table_orders`, `update_status`(ALLOWED_TRANSITIONS 위반 시 409), `delete_order`(총액 재계산 + 이벤트).
- `router.py` — 대시보드 REST + SSE 스트림(`GET /api/sse/dashboard`, `_event_stream` async 제너레이터, 20초 하트비트, `X-Accel-Buffering: no`).

## 규칙 (검증됨)
- 상태 전이 단방향(대기중→준비중→완료), 위반 409.
- 대시보드 총액 = 미종료 주문 합계.
- 이벤트는 커밋 이후 dashboard/session 토픽에 발행.

## 테스트 (`backend/tests/test_transitions_and_menu.py`)
- 완료→이전 전이 거부(PBT).
