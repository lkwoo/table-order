# U6-menu-management — 코드 요약

관리자 메뉴 CRUD 및 순서 변경.

## 생성 파일 (`backend/app/menu_mgmt/`)
- `schemas.py` — `MenuCreate`/`MenuUpdate`(가격 1,000~100,000 검증), `ReorderRequest`, `AdminMenuOut`.
- `service.py` — `list_admin_menus`(비활성 포함 전체), `create_menu`(display_order=최대+1), `update_menu`, `soft_delete_menu`(is_active=false), `reorder_menus`(집합 일치 검증 후 일괄, 부분 적용 금지 R5).
- `router.py` — Bearer 인증. `reorder` 경로를 `/{menu_id}` 보다 먼저 선언(경로 충돌 방지).

## 규칙 (검증됨)
- reorder 후 `display_order` 는 0..n-1 연속·유일.
- 소프트 삭제 메뉴는 고객 조회 제외, 기존 주문 스냅샷은 유지.

## 테스트 (`backend/tests/test_transitions_and_menu.py`)
- reorder 연속성(PBT), 소프트 삭제 후 고객 제외 + 스냅샷 유지.
