# Business Logic Model - U6 Menu Management

**작성일**: 2026-08-31 | **Unit**: U6 | **스토리**: A9~A13

---

## 워크플로우 1: 메뉴 조회(관리자, A9)
```
입력: AdminContext(store_id)
- is_active 무관 전체(또는 활성 위주) 카테고리별 조회, display_order 정렬
- 각 메뉴: 이미지, 명, 가격, 카테고리, 설명, 수정/삭제 액션
```

## 워크플로우 2: 메뉴 등록 (A10)
```
입력: { name, price, category_id, description?, image_url? }
1. 검증: 필수(name, price, category), price 1,000~100,000, category 존재
2. display_order = 해당 카테고리 마지막+1 (기본 말미 배치)
3. [TX] Menu 생성(is_active=true)
4. 반환: 생성된 메뉴
```

## 워크플로우 3: 메뉴 수정 (A11)
```
입력: menu_id, 수정 필드
1. Menu 조회(store_id 일치) → 없으면 404
2. 검증(등록과 동일)
3. [TX] 갱신, updated_at, 변경 로그
4. 반환: 갱신 메뉴
(고객 화면은 다음 조회 시 반영)
```

## 워크플로우 4: 메뉴 삭제 (A12) — 소프트 삭제
```
입력: menu_id
1. Menu 조회
2. [TX] is_active=false 설정(Q7 소프트 삭제), 삭제 로그
   → 고객 목록에서 숨김, 기존 주문/이력의 스냅샷은 영향 없음
3. 반환: 성공
```

## 워크플로우 5: 노출 순서 조정 (A13)
```
입력: category_id, ordered_menu_ids: [...]
1. 해당 카테고리 소속 검증
2. [TX] 각 메뉴 display_order = 배열 인덱스로 일괄 갱신
     실패 시 롤백(기존 순서 유지)
3. 반환: 성공 (고객 C3에 다음 조회 시 반영)
```

---

## 통합 지점
- U0: MenuRepository, MenuCategory, AuthGuard(관리자).
- U2 Menu(고객 조회)가 결과를 소비. 실시간 push 없음(조회 시 반영).

## 오류 시나리오
| 상황 | 처리 |
|------|------|
| 필수 필드 누락 | 422 |
| 가격 범위 밖 | 422 |
| 존재하지 않는 카테고리 | 422 |
| 없는 메뉴 수정/삭제 | 404 |
| 순서 조정 중 오류 | 롤백 + 오류 |
