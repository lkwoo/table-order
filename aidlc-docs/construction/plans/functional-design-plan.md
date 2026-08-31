# Functional Design Plan - 테이블오더 서비스 (전체 Unit)

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - Functional Design
**범위**: 8개 Unit(U0~U7)의 상세 비즈니스 로직 설계 (기술 무관, 도메인 중심)

---

## 개요

Application Design(고수준)과 Units Generation(단위 분해)을 기반으로, 각 Unit의 **상세 비즈니스 로직·도메인 모델·비즈니스 규칙**을 설계합니다. 인프라 관심사는 제외합니다.

Unit별로 다음 산출물을 생성합니다 (해당되는 경우):
- `business-logic-model.md` — 핵심 워크플로우/알고리즘
- `business-rules.md` — 결정 규칙, 검증, 제약
- `domain-entities.md` — 엔티티/속성/관계
- `frontend-components.md` — (U7만) 컴포넌트 계층, props/state, 상호작용, 폼 검증, API 연동

**핵심 복잡 로직**(집중 설계 대상): 주문 상태 전이(U4), 세션 종료 원자적 이력 이동(U5), 세션 격리(U3), 자동 재시도(U3/U7), 인증 토큰 수명(U1).

---

# PART 1: PLANNING - 체크리스트

## Step 1: Unit 컨텍스트 분석 ✅
- [x] unit-of-work.md / story-map 분석

## Step 2: 결정 질문 답변 (아래 PART 2) ✅
- [x] 모든 [Answer]: 태그 작성 (전부 A/권장, 모호성 없음)

## Step 3: 산출물 생성 (승인 후) ✅
- [x] U0 Core: domain-entities.md (9 엔티티 통합 스키마) + business-rules.md (공통 검증/제약)
- [x] U1 Auth: business-logic-model / business-rules
- [x] U2 Menu: business-logic-model / business-rules
- [x] U3 Order: business-logic-model / business-rules
- [x] U4 Realtime & Dashboard: business-logic-model / business-rules
- [x] U5 Table & Session: business-logic-model / business-rules
- [x] U6 Menu Management: business-logic-model / business-rules
- [x] U7 Frontend: frontend-components.md

---

# PART 2: 비즈니스 로직 결정 질문

각 `[Answer]:` 태그 뒤에 답변해주세요. 권장값(⭐) 있음, "전부 권장" 일괄 가능.

---

## Q1. 주문 상태 전이 규칙 (Business Rules — U4)

주문 상태 흐름과 되돌리기 정책은?

- **A) 대기중 → 준비중 → 완료, 단방향 전진만 허용** ⭐권장
  - 역방향(완료→준비중) 불가. 잘못된 경우 삭제(A6)로 처리
- **B) 자유 전이 (임의 상태 변경 허용)**
- **C) 전진 + 인접 1단계 되돌리기 허용**

[Answer]: A

---

## Q2. 주문 번호 생성 방식 (Business Logic — U3)

고객에게 보여줄 주문 번호를 어떻게 생성할까요?

- **A) 매장 내 일련번호 (매장별 1씩 증가, 예: #1024)** ⭐권장
  - 관리자·고객 모두 이해 쉬움. 세션 종료와 무관하게 매장 스코프로 연속
- **B) 랜덤/UUID 단축코드**
- **C) 테이블별 일련번호**

[Answer]: A

---

## Q3. 세션 종료 시 이력 이동 방식 (Business Rules — U5)

세션 종료(A7) 시 현재 주문의 이력화 방식은?

- **A) 주문+주문항목 스냅샷을 OrderHistory로 복사(메뉴명/가격 포함) 후 현재 주문 삭제** ⭐권장
  - 메뉴가 나중에 변경/삭제돼도 이력 보존(참조 무결성). 3개월 보관
- **B) 참조만 유지 (메뉴 변경 시 이력도 변함)**

[Answer]: A

---

## Q4. 세션 격리 키 (Business Logic — U3)

주문을 세션에 귀속시키는 기준은?

- **A) TableSession.id (세션 생성 시마다 새 UUID)** ⭐권장
  - 주문은 생성 시점의 활성 세션 id에 연결. 조회는 현재 세션 id로 필터(C12)
- **B) table_id + 시간 범위**

[Answer]: A

---

## Q5. 장바구니 검증 시점 (Business Rules — U3/U7)

장바구니→주문 확정 시 가격/메뉴 유효성 검증은 어디서?

- **A) 서버가 주문 생성 시점에 재검증(가격/존재 여부 서버 기준으로 확정)** ⭐권장
  - 클라이언트 가격은 표시용, 최종 금액은 서버가 메뉴 테이블 기준 계산(위변조 방지)
- **B) 클라이언트 금액을 신뢰**

[Answer]: A

---

## Q6. 자동 재시도 대상 (Error Handling — U3/U7)

네트워크 오류 자동 재시도(최대 3회)를 어떤 요청에 적용할까요?

- **A) 멱등/안전 요청 + 주문 생성(멱등키 사용)** ⭐권장
  - 주문 생성은 클라이언트 생성 idempotency-key로 중복 주문 방지하며 재시도
- **B) 모든 요청 무조건 재시도 (중복 위험)**

[Answer]: A

---

## Q7. 메뉴 삭제와 진행 중 주문 (Business Rules — U6)

메뉴 삭제(A12) 시 현재 주문/이력 처리는?

- **A) 소프트 삭제(비노출 플래그) — 현재/과거 주문의 메뉴 참조 보존** ⭐권장
  - 고객 메뉴 목록에서만 숨김. 주문·이력은 스냅샷/참조 유지
- **B) 하드 삭제 + 이력은 스냅샷으로만 보존**

[Answer]: A

---

## Q8. 프론트엔드 상태 관리 (Frontend — U7)

React 상태 관리 방식은?

- **A) 경량: Context + hooks (+ 장바구니는 localStorage 동기화)** ⭐권장
  - 프로토타입 규모에 적합, 외부 라이브러리 최소화
- **B) Redux 등 전역 상태 라이브러리 도입**

[Answer]: A

---

## Q9. 오프라인 재동기화 상세 (Business Logic — U4/U7)

관리자 대시보드 재연결 시 동기화 방식은?

- **A) 재연결 시 대시보드 전체 스냅샷 REST 재조회로 갱신 (last-write-wins)** ⭐권장
  - 단순·정확. 놓친 이벤트를 개별 재생하지 않고 최신 상태로 덮어씀
- **B) 이벤트 로그 재생 (누락 이벤트 순차 반영)**

[Answer]: A

---

# PART 3: 다음 지침

1. Q1~Q9의 [Answer]: 태그에 답변해주세요 ("전부 권장" 가능).
2. 답변 완료 후 알려주세요. 모호하면 후속 질문 드립니다.
3. 확정 시 Unit별 Functional Design 산출물을 생성합니다.

---

**작성일**: 2026-08-31
**상태**: 답변 완료 (전부 권장) → 산출물 생성 완료
