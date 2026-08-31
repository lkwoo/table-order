# Domain Entities - U0 Core (통합 스키마)

**작성일**: 2026-08-31
**Unit**: U0 Core/Shared
**범위**: 전 Unit이 공유하는 9개 도메인 엔티티. 기술 무관 개념 모델(구현 시 SQLAlchemy 매핑).

---

## 엔티티 관계 개요

```
Store 1─N Admin
Store 1─N Table 1─N TableSession 1─N Order 1─N OrderItem
Store 1─N MenuCategory 1─N Menu
Menu 1─N OrderItem (참조, 스냅샷 병행)
Table 1─N OrderHistory 1─N OrderHistoryItem (스냅샷)
```

---

## 1. Store (매장)
| 속성 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | UUID | PK | |
| name | string | required | 매장명 |
| created_at | datetime | | |

관계: 1:N Admin, Table, MenuCategory, Menu.

## 2. Admin (관리자)
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK |
| store_id | UUID | FK Store, required |
| username | string | required, unique(store_id, username) |
| password_hash | string | bcrypt |
| created_at | datetime | |

로그인 키: (store_id, username). 1 매장당 관리자 존재(요구사항: 1 store per admin).

## 3. Table (테이블)
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK |
| store_id | UUID | FK Store |
| table_number | string | required, unique(store_id, table_number) |
| password_hash | string | bcrypt, 4~10자리 원문 규칙 |
| created_at | datetime | |

관계: 1:N TableSession, OrderHistory.

## 4. TableSession (테이블 세션) — 세션 격리 핵심
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK (= 세션 격리 키, Q4) |
| table_id | UUID | FK Table |
| token | string | 세션 토큰(고객 태블릿 저장) |
| status | enum(active, ended) | |
| created_at | datetime | |
| expires_at | datetime | created_at + 16h |
| ended_at | datetime\|null | 종료 시각 |

규칙: table당 active 세션 최대 1개. 주문은 생성 시점 active 세션 id에 귀속.

## 5. MenuCategory (메뉴 카테고리)
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK |
| store_id | UUID | FK Store |
| name | string | required (예: 음료, 메인) |
| display_order | int | 카테고리 정렬 |

## 6. Menu (메뉴)
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK |
| store_id | UUID | FK Store |
| category_id | UUID | FK MenuCategory |
| name | string | required |
| price | int(KRW) | required, 1,000~100,000 |
| description | text | optional |
| image_url | string | optional, 외부 URL |
| display_order | int | 카테고리 내 정렬(A13) |
| is_active | bool | 소프트 삭제 플래그(Q7), default true |
| created_at / updated_at | datetime | |

## 7. Order (현재 주문)
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK |
| store_id | UUID | FK Store |
| table_id | UUID | FK Table |
| session_id | UUID | FK TableSession (격리 키) |
| order_number | int | 매장 스코프 일련번호(Q2) |
| status | enum(대기중, 준비중, 완료) | default 대기중 |
| total_amount | int | 서버 계산(Q5) |
| idempotency_key | string | unique, 중복 주문 방지(Q6) |
| created_at | datetime | |
| updated_at | datetime | 상태 변경 시각 |

관계: 1:N OrderItem.

## 8. OrderItem (주문 항목)
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK |
| order_id | UUID | FK Order |
| menu_id | UUID | FK Menu (참조) |
| menu_name | string | 스냅샷(주문 시점 명칭) |
| unit_price | int | 스냅샷(주문 시점 가격) |
| quantity | int | 1~99 |
| subtotal | int | unit_price × quantity |

## 9. OrderHistory (과거 주문 이력) + OrderHistoryItem
세션 종료 시 Order/OrderItem을 스냅샷 복사(Q3). 3개월 보관(요구사항 4.4).

**OrderHistory**
| 속성 | 타입 | 제약 |
|------|------|------|
| id | UUID | PK |
| store_id / table_id | UUID | FK |
| original_session_id | UUID | 어떤 세션이었는지 |
| order_number | int | 원본 주문번호 |
| final_status | enum | 이력화 시점 상태 |
| total_amount | int | |
| ordered_at | datetime | 원본 주문 시각 |
| completed_at | datetime\|null | 완료 시각 |
| archived_at | datetime | 이력 이동 시각 |

**OrderHistoryItem**
| 속성 | 타입 |
|------|------|
| id | UUID PK |
| history_id | FK OrderHistory |
| menu_name | string (스냅샷) |
| unit_price | int (스냅샷) |
| quantity | int |
| subtotal | int |

> 스냅샷 저장으로 메뉴 수정/삭제와 무관하게 이력 보존(참조 무결성).

---

## 인덱스/조회 최적화 (성능 요구사항 대응)
- Order: `(store_id, table_id)`, `(session_id)`, `(store_id, order_number)` 인덱스
- Menu: `(store_id, category_id, display_order)` 인덱스 (메뉴 로드 <2초)
- OrderHistory: `(table_id, archived_at)` 인덱스 (이력 조회/날짜 필터)
- TableSession: `(table_id, status)` 인덱스 (active 세션 조회)

---

**상태**: 검토 대기
