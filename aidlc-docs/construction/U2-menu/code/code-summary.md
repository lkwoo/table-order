# U2-menu — 코드 요약

고객용 메뉴 조회(활성 메뉴만).

## 생성 파일 (`backend/app/menu/`)
- `schemas.py` — `MenuItemOut`, `MenuCategoryOut`.
- `repository.py` — `list_categories`, `list_menus(active_only)`, `get_menu`.
- `service.py` — `list_menu_by_category`(활성 메뉴를 카테고리별 그룹화), `get_menu_detail`(비활성 시 404).
- `router.py` — `GET /api/menus`, `GET /api/menus/{menu_id}` (세션 인증).

## 규칙
- 소프트 삭제(is_active=false) 메뉴는 고객 조회에서 제외.
- `display_order` 오름차순 정렬.
