# NFR Requirements Plan - 테이블오더 서비스 (프로젝트 레벨)

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - NFR Requirements
**범위**: 모놀리스 단일 서비스의 횡단 비기능 요구사항 (8개 Unit 공통)

---

## 개요

Functional Design과 승인된 requirements §4(비기능 요구사항)를 기반으로, 시스템 전반의 **비기능 요구사항(NFR)과 기술 스택 결정**을 확정합니다. 대부분의 NFR은 이미 requirements 단계에서 명시/승인되었으므로, 본 단계는 이를 정량화하고 설계에 반영할 수 있는 형태로 정리합니다.

---

# PART 1: PLANNING - 체크리스트

## Step 1: Functional Design 분석 ✅
- [x] 8개 Unit functional-design 산출물 검토
- [x] requirements §4 (성능/가용성/보안/데이터/확장성) 매핑

## Step 2: 결정 질문 답변 (아래 PART 2) ✅
- [x] 모든 [Answer]: 태그 작성 (전부 권장, 근거=requirements §4)

## Step 3: 산출물 생성 ✅
- [x] `nfr-requirements/nfr-requirements.md`
- [x] `nfr-requirements/tech-stack-decisions.md`

---

# PART 2: NFR 결정 질문

각 `[Answer]:` 태그는 승인된 requirements §4에 근거한 권장값(⭐)으로 채워졌습니다.

---

## Q1. 성능 목표 정량화 (Performance)

성능 SLA를 어떻게 확정할까요?

- **A) 주문 생성 p95 <1s, 메뉴 로드 p95 <2s, SSE end-to-end <2s** ⭐권장
  - requirements §4.1 그대로. 로컬/단일 인스턴스 기준, 정상 부하(20-30 동시)에서 측정
- **B) 더 엄격한 목표 (p99 기준)**
- **C) 목표 미설정 (best-effort)**

[Answer]: A

---

## Q2. 확장 규모 및 스케일링 (Scalability)

초기 용량과 스케일링 전략은?

- **A) 10-20 테이블, 동시 20-30 세션 / 단일 인스턴스 (수직 확장), 인메모리 EventBroker** ⭐권장
  - requirements §4.5. MVP·프로토타입 규모. 수평 확장(멀티 인스턴스 SSE)은 범위 밖
- **B) 멀티 인스턴스 대비 (Redis Pub/Sub 등 외부 브로커)**

[Answer]: A

---

## Q3. 가용성 목표 (Availability)

가용성/복구 요구는?

- **A) 단일 인스턴스, 정식 SLA 없음(프로토타입). 대시보드 오프라인 캐싱 + 재연결 시 스냅샷 재동기화** ⭐권장
  - requirements §4.2. 무중단·자동 페일오버는 범위 밖. DB 트랜잭션으로 정합성 보장
- **B) HA 구성 (다중 인스턴스 + 헬스체크 + 자동 페일오버)**

[Answer]: A

---

## Q4. 보안 수준 (Security)

보안 요구 범위는?

- **A) bcrypt 해싱 + JWT(16h) + 전 입력 검증 + 프로덕션 HTTPS (기본 애플리케이션 보안)** ⭐권장
  - requirements §4.3. Security Baseline extension은 off(프로토타입)이나 위 항목은 필수 기본으로 포함
- **B) Security Baseline extension 활성화 (레이트리밋, 감사로그, 위협모델 전면 적용)**

[Answer]: A

---

## Q5. 신뢰성 / 오류 처리 (Reliability)

정합성·재시도 정책은?

- **A) idempotency-key 기반 주문 재시도(최대 3회) + 세션 종료 단일 원자 트랜잭션 + 서버측 금액 재검증** ⭐권장
  - Functional Design(Q5/Q6/Q3) 결정과 정합. 중복 주문·부분 이관 방지
- **B) 재시도 없이 사용자 수동 재시도만**

[Answer]: A

---

## Q6. 데이터 수명주기 (Data Management)

데이터 보관·격리 정책은?

- **A) OrderHistory 3개월 보관, TableSession.id 기반 세션 격리, 트랜잭션 사용** ⭐권장
  - requirements §4.4. 3개월 경과 이력 정리(향후 배치/수동)는 Operations 단계로 이연
- **B) 무기한 보관**

[Answer]: A

---

## Q7. 유지보수/관측성 (Maintainability & Observability)

코드 품질·관측 수준은?

- **A) 계층형(Router→Service→Repository) + OpenAPI 자동 문서 + 구조적 로깅(stdout) + PBT(주문/결제 정합성)** ⭐권장
  - 프로토타입 규모에 적합. 메트릭/트레이싱/알림 등 풀 관측성은 Operations로 이연
- **B) 전면 관측성 스택(Prometheus/Grafana/분산추적) 도입**

[Answer]: A

---

## Q8. 사용성/접근성 (Usability)

프론트엔드 사용성 목표는?

- **A) 태블릿(고객) + 데스크톱(관리자) 반응형, 터치 친화 UI, 이미지 lazy-load** ⭐권장
  - requirements §3.1.2(이미지 최적화), §3.2.2(카드 그리드). WCAG 전면 준수는 범위 밖(기본 대비/폰트만)
- **B) WCAG 2.1 AA 전면 준수**

[Answer]: A

---

# PART 3: 다음 지침

1. 위 답변은 승인된 requirements §4에 근거한 권장값으로 사전 확정되었습니다.
2. 변경을 원하시면 해당 [Answer]: 태그를 수정 요청해주세요.
3. 확정 기준으로 `nfr-requirements/` 산출물을 생성합니다.

---

**작성일**: 2026-08-31
**상태**: 답변 완료 (전부 권장, requirements §4 근거) → 산출물 생성 완료
