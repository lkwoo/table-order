# Unit of Work ↔ Story Map - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Units Generation

---

## 1. 스토리 → Unit 매핑 (전체 24개)

| Story | 스토리명 | 주 Unit(백엔드) | UI Unit | Sprint |
|-------|----------|----------------|---------|--------|
| C1 | 테이블 자동 로그인 | U1 Auth | U7 | S1 |
| C2 | 테이블 초기 설정 로그인 | U1 Auth | U7 | S1 |
| C3 | 메뉴 리스트 조회 | U2 Menu | U7 | S1 |
| C4 | 메뉴 상세 조회 | U2 Menu | U7 | S1 |
| C6 | 장바구니 추가 | (클라이언트) | U7 | S1 |
| C7 | 장바구니 수량 조절 | (클라이언트) | U7 | S1 |
| C8 | 장바구니 제거 | (클라이언트) | U7 | S1 |
| C9 | 주문 전 최종 확인 | (클라이언트) | U7 | S1 |
| C10 | 주문 생성 | U3 Order | U7 | S1 |
| C11 | 현재 세션 주문 조회 | U3 Order (+U4 SSE) | U7 | S1 |
| C12 | 이전 세션 제외(격리) | U3 Order | U7 | S1 |
| A1 | 관리자 로그인 | U1 Auth | U7 | S1 |
| A2 | 실시간 대시보드 | U4 Realtime | U7 | S1 |
| A3 | 테이블 상세 주문 보기 | U4 Realtime | U7 | S1 |
| A4 | 주문 상태 변경 | U4 Realtime | U7 | S1 |
| A5 | 테이블 초기 설정(관리자) | U5 Table | U7 | S1 |
| A6 | 주문 삭제 | U4 Realtime | U7 | S1 |
| A7 | 테이블 세션 종료 | U5 Table | U7 | S1 |
| A8 | 과거 주문 이력 조회 | U5 Table | U7 | S1 |
| A9 | 메뉴 조회(관리자) | U6 MenuMgmt | U7 | S2 |
| A10 | 메뉴 등록 | U6 MenuMgmt | U7 | S2 |
| A11 | 메뉴 수정 | U6 MenuMgmt | U7 | S2 |
| A12 | 메뉴 삭제 | U6 MenuMgmt | U7 | S2 |
| A13 | 메뉴 노출 순서 조정 | U6 MenuMgmt | U7 | S2 |

> C5는 결번(범위 밖 제거). U0 Core는 횡단 지원 Unit으로 특정 스토리에 직접 대응하지 않음.

---

## 2. Unit → 스토리 요약

| Unit | 스토리 수 | 스토리 | Sprint |
|------|----------|--------|--------|
| **U0 Core** | (횡단) | 전 스토리 기반 지원 | S1 |
| **U1 Auth** | 3 | A1, C1, C2 | S1 |
| **U2 Menu** | 2 | C3, C4 | S1 |
| **U3 Order** | 3(+장바구니 UI 4) | C10, C11, C12 (C6-C9는 UI) | S1 |
| **U4 Realtime & Dashboard** | 4 | A2, A3, A4, A6 | S1 |
| **U5 Table & Session** | 3 | A5, A7, A8 | S1 |
| **U6 Menu Management** | 5 | A9, A10, A11, A12, A13 | S2 |
| **U7 Frontend** | 24(UI) | 전 스토리 UI | S1~S2 |

---

## 3. Sprint별 Unit 개발 계획

### Sprint 1 (MVP, 19 스토리)
- **U0 Core** → 기반 (DB, 모델, 가드, EventBroker)
- **U1 Auth** → C1, C2, A1
- **U2 Menu** → C3, C4
- **U3 Order** → C10, C11, C12
- **U4 Realtime** → A2, A3, A4, A6
- **U5 Table** → A5, A7, A8
- **U7 Frontend** (S1 범위) → 고객 전체 + 관리자 대시보드/테이블 관리

### Sprint 2 (5 스토리)
- **U6 Menu Management** → A9~A13
- **U7 Frontend** (S2 범위) → 관리자 메뉴 관리 화면

---

## 4. 검증

| 항목 | 상태 |
|------|------|
| 24개 스토리 전부 매핑? | ✅ |
| 각 스토리 백엔드/UI Unit 명시? | ✅ |
| Sprint 배치가 stories.md와 일치? | ✅ (S1:19, S2:5) |
| C5 결번 처리 반영? | ✅ |

---

**작성일**: 2026-08-31
**상태**: 검토 대기
