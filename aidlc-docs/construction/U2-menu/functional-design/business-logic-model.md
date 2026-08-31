# Business Logic Model - U2 Menu (고객 조회)

**작성일**: 2026-08-31 | **Unit**: U2 Menu | **스토리**: C3(목록), C4(상세)

---

## 워크플로우 1: 메뉴 목록 조회 (C3)
```
입력: TableSessionContext (store_id 도출)
1. MenuCategory 목록 조회 (store_id, display_order 정렬)
2. Menu 조회: is_active=true, category별 display_order 정렬 (Q7 소프트 삭제 반영)
3. 카테고리별 그룹핑 구조 반환:
   [{ category, menus: [{ id, name, price, description, image_url }] }]
```
- 성능: <2초. `(store_id, category_id, display_order)` 인덱스 활용.
- image_url 없으면 프론트가 기본 아이콘 표시.

## 워크플로우 2: 메뉴 상세 조회 (C4)
```
입력: menu_id (+ 세션 컨텍스트)
1. Menu 조회, is_active=true & store_id 일치 확인
2. 없거나 비활성 → 404
3. 반환: { name, price, description, image_url }  (요구사항 3.1.2)
```

---

## 데이터 흐름
- 읽기 전용. 부작용 없음.
- 정렬은 A13(순서 조정)의 display_order를 그대로 반영 → 관리자 변경이 즉시 고객에 노출.

## 통합 지점
- U0: MenuRepository, MenuCategory. AuthGuard(고객 세션).
- U6 Menu Management가 변경한 데이터를 조회(별도 실시간 push 불필요, 다음 조회 시 반영).

## 오류 시나리오
- 비활성/삭제 메뉴 상세 요청 → 404
- 빈 카테고리 → 빈 배열 반환(정상)
