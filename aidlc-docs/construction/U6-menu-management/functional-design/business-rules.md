# Business Rules - U6 Menu Management

**작성일**: 2026-08-31 | **Unit**: U6

---

| # | 규칙 |
|---|------|
| R1 | 필수 필드: name, price, category. 누락 시 422 |
| R2 | 가격 1,000~100,000 정수(KRW) |
| R3 | 삭제는 **소프트 삭제**(is_active=false) — 주문/이력 참조 보존(Q7) |
| R4 | display_order는 카테고리 내에서만 의미. 순서 조정은 카테고리 단위 일괄 갱신 |
| R5 | 순서 조정 실패 시 전체 롤백(부분 적용 금지) |
| R6 | 수정/삭제는 변경 로그 기록 |
| R7 | image_url은 외부 URL 문자열만 저장(업로드/리사이징 없음 — 범위 밖) |
| R8 | 모든 작업은 store_id 스코프 |

## Property-Based Test 후보
- 임의 순서 배열 적용 후 display_order가 0..n-1 연속·유일
- 소프트 삭제된 메뉴는 고객 조회(U2)에 나타나지 않으나 기존 OrderItem 스냅샷은 유지
