# U5-table — 코드 요약

테이블 관리(생성) 및 세션 종료·이력 조회.

## 생성 파일 (`backend/app/table_session/`)
- `schemas.py` — `TableCreate`(비밀번호 4~10자 검증), `HistoryOut`.
- `service.py` — `create_table`(중복 409), `end_session`(단일 트랜잭션: 이력 스냅샷 + 주문 삭제 + 새 세션 생성 + `session.ended` 이벤트), `list_history`(`_date_range` 필터 + 3개월 보관).
- `router.py` — Bearer 인증, `POST /api/admin/tables`, `GET /api/admin/tables`, `POST /api/admin/tables/{id}/end-session`, `GET /api/admin/tables/{id}/history?filter=&from=&to=`.

## 규칙 (검증됨)
- 세션 종료 시 현재 주문 합계 == 이력에 보존된 합계(보존), 종료 후 새 active 세션 1개, 기존은 ended.
- 이력 필터: all/today/yesterday + 기간, 90일 초과 제외.

## 테스트 (`backend/tests/test_pbt_session.py`)
- 세션 종료 합계 보존 + 세션 격리(PBT).
