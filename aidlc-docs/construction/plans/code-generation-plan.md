# Code Generation Plan - 테이블오더 서비스 (통합)

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - Code Generation
**프로젝트 유형**: Greenfield 모놀리스
**코드 위치**: 워크스페이스 루트 (`backend/`, `frontend/`) — **절대 aidlc-docs/ 아님**
**단일 진실 원천(SSOT)**: 본 문서

---

## 생성 순서 (의존성 기반: U0 → U1 → U2/U6 → U3 → U4/U5 → U7)

| 단계 | Unit | 산출물 | 스토리 |
|------|------|-------|-------|
| 1 | U0 Core | config, db, security(guard/JWT/bcrypt), event_broker, models(9 엔티티), base schemas | 인프라 |
| 2 | U1 Auth | admin-login, table-login, verify, guards | A1, C1, C2 |
| 3 | U2 Menu | 고객 메뉴 조회 | C3, C4 |
| 4 | U6 Menu Mgmt | 메뉴 CRUD + reorder | A9-A13 |
| 5 | U3 Order | 주문 생성(멱등키/서버재계산), 조회(격리) | C10, C11, C12 |
| 6 | U4 Realtime | 대시보드, 상태변경, 삭제, SSE 스트림 | A2-A4, A6 |
| 7 | U5 Table | 테이블 설정, 세션종료(원자TX), 이력조회 | A5, A7, A8 |
| 8 | U7 Frontend | React 고객/관리자 앱 | 전 스토리 |
| 9 | 인프라 | docker-compose, Dockerfile×2, .env.example, README | — |
| 10 | 테스트 | pytest + Hypothesis(PBT 불변식) | — |

---

## REST API 계약 (프론트/백엔드 통합 기준)

Base URL: `/api`

### 인증 (U1)
| Method | Path | 인증 | Body | 응답 |
|--------|------|------|------|------|
| POST | `/api/auth/admin-login` | - | `{store_id, username, password}` | `{access_token, token_type, expires_at, store_id, admin_id}` |
| GET | `/api/auth/admin-verify` | Bearer | - | `{admin_id, store_id}` |
| POST | `/api/auth/table-login` | - | `{store_id, table_number, password}` | `{session_token, table_id, session_id, expires_at}` |
| GET | `/api/auth/table-verify` | Session | - | `{table_id, session_id, store_id, expires_at}` |

### 고객 메뉴 (U2) — Session 토큰
| GET | `/api/menus` | Session | - | `[{category_id, category_name, display_order, menus:[{id,name,price,description,image_url}]}]` |
| GET | `/api/menus/{menu_id}` | Session | - | `{id,name,price,description,image_url}` |

### 고객 주문 (U3) — Session 토큰
| POST | `/api/orders` | Session | `{idempotency_key, items:[{menu_id, quantity}]}` | `{id, order_number, status, total_amount, items:[...], created_at}` |
| GET | `/api/orders` | Session | - | `[{id, order_number, status, total_amount, items:[{menu_name,unit_price,quantity,subtotal}], created_at}]` (현재 세션, 시간역순) |

### 고객 SSE (U4)
| GET | `/api/sse/orders` | Session(쿼리 `token=`) | - | text/event-stream: `order.status_changed`, `order.deleted` |

### 관리자 대시보드/주문 (U4) — Bearer
| GET | `/api/admin/dashboard` | Bearer | - | `[{table_id, table_number, total_amount, recent_orders:[{order_number,status,summary}], has_new:false}]` |
| GET | `/api/admin/tables/{table_id}/orders` | Bearer | - | `[{id, order_number, status, total_amount, items:[...], created_at}]` |
| PATCH | `/api/admin/orders/{order_id}/status` | Bearer | `{status}` | `{id, status, ...}` (전이 위반 409) |
| DELETE | `/api/admin/orders/{order_id}` | Bearer | - | `{table_id, table_total}` |
| GET | `/api/sse/dashboard` | Bearer(쿼리 `token=`) | - | event-stream: `order.created`, `order.status_changed`, `order.deleted`, `session.ended` |

### 관리자 테이블/세션 (U5) — Bearer
| POST | `/api/admin/tables` | Bearer | `{table_number, password}` | `{table_id, table_number, session_id}` (중복 409) |
| GET | `/api/admin/tables` | Bearer | - | `[{table_id, table_number}]` |
| POST | `/api/admin/tables/{table_id}/end-session` | Bearer | - | `{table_id, archived_count}` |
| GET | `/api/admin/tables/{table_id}/history` | Bearer | `?filter=all|today|yesterday&from=&to=` | `[{order_number, ordered_at, completed_at, total_amount, items:[...]}]` |

### 관리자 메뉴 관리 (U6) — Bearer
| GET | `/api/admin/menus` | Bearer | - | 카테고리별(is_active 포함) |
| GET | `/api/admin/categories` | Bearer | - | `[{id, name, display_order}]` |
| POST | `/api/admin/menus` | Bearer | `{name, price, category_id, description?, image_url?}` | 생성 메뉴 |
| PUT | `/api/admin/menus/{menu_id}` | Bearer | 수정 필드 | 갱신 메뉴 |
| DELETE | `/api/admin/menus/{menu_id}` | Bearer | - | `{id, is_active:false}` (소프트 삭제) |
| PATCH | `/api/admin/menus/reorder` | Bearer | `{category_id, ordered_menu_ids:[...]}` | `{updated:n}` |

### 공통
| GET | `/health` | - | - | `{status:"ok"}` |

**상태값**: `대기중`, `준비중`, `완료`. 전이: 대기중→{준비중,완료}, 준비중→완료 (역방향 409).
**오류**: 422 검증 / 401 인증 / 403 타매장 / 404 없음 / 409 중복·전이위반 / 500.
**금액**: 정수 KRW. 서버가 Menu.price로 재계산.

---

## 디렉터리 구조

```
backend/app/{main.py, core/, auth/, menu/, order/, realtime/, table_session/, menu_mgmt/}
  각 도메인: models.py 조각(또는 core/models.py 통합), schemas.py, repository.py, service.py, router.py
backend/{tests/, alembic/, Dockerfile, requirements.txt, alembic.ini, seed.py}
frontend/{src/{shared/, customer/, admin/, App.tsx, main.tsx}, Dockerfile, package.json, vite.config.ts, index.html}
docker-compose.yml, .env.example, README.md
```

**구현 결정**: 모델은 `core/models.py`에 9개 엔티티 통합(단일 Base, Alembic 단일 체인). 스키마 초기화는 앱 기동 시 `Base.metadata.create_all` + 시드(프로토타입 단순화; Alembic 파일도 제공).

---

## 스토리 추적성

- C1,C2,A1 → U1 | C3,C4 → U2 | C6-C12,A* → 각 Unit(위 표) | 전 UI → U7
- C5 = 결번(범위 밖 제거됨)

---

## PBT 불변식 (Build&Test에서 실행)
1. `total_amount == Σ(unit_price×quantity)`
2. 동일 idempotency_key N회 → 주문 1건
3. 세션 격리: 세션A 조회에 세션B 주문 없음
4. 세션 종료: 이관 합계 == 종료 전 현재주문 합계, 종료 후 현재주문 0
5. 상태 전이: 완료→이전 항상 거부
6. reorder 후 display_order 0..n-1 연속·유일
7. 소프트 삭제 메뉴는 고객 조회 제외, 기존 스냅샷 유지

---

**상태**: 승인됨 (사용자 "진행해줘" 2026-08-31) → 생성 진행
