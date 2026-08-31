# NFR Requirements - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - NFR Requirements
**범위**: 프로젝트 레벨 (모놀리스, 8개 Unit 공통 횡단 NFR)
**근거**: 승인된 `requirements.md §4` + Functional Design 결정

---

## 1. 성능 (Performance)

| ID | 요구사항 | 목표 | 측정 조건 | 관련 Unit |
|----|---------|------|----------|----------|
| P1 | 주문 생성 응답 시간 | p95 < 1초 | 정상 부하(동시 20-30), 로컬 단일 인스턴스 | U3 Order |
| P2 | 메뉴 목록 로드 | p95 < 2초 | 카테고리 포함 전체 메뉴 조회 | U2 Menu |
| P3 | SSE 상태 반영 (end-to-end) | < 2초 | 관리자 상태 변경 → 고객 화면 반영 | U4 Realtime |
| P4 | 신규 주문 대시보드 반영 | < 2초 | 주문 생성 → 관리자 대시보드 카드 갱신 | U4 Realtime |
| P5 | 이미지 로딩 | lazy-load, 태블릿 최적화 | 외부 URL, 뷰포트 진입 시 로드 | U7 Frontend |

**부하 가정**: 매장당 10-20 테이블, 동시 활성 세션 20-30, 초당 주문 생성 ≤ 5 TPS (피크).

---

## 2. 확장성 (Scalability)

| ID | 요구사항 | 결정 |
|----|---------|------|
| S1 | 테이블 수 | 매장당 10-20개 (초기) |
| S2 | 동시 사용자 | 20-30 (태블릿 + 관리자) |
| S3 | 배포 토폴로지 | **단일 인스턴스 (수직 확장)** — 인메모리 EventBroker로 SSE 처리 |
| S4 | DB 확장 | PostgreSQL 단일 인스턴스, 인덱스 기반 조회 최적화 |
| S5 | 범위 밖 | 멀티 인스턴스 SSE(외부 Pub/Sub), 멀티 매장 샤딩 — Operations/향후 |

**근거**: MVP·프로토타입. 단일 인스턴스 인메모리 EventBroker는 20-30 동시 SSE 연결에 충분(Application Design Q4 결정과 정합).

---

## 3. 가용성 (Availability)

| ID | 요구사항 | 결정 |
|----|---------|------|
| A1 | 가동 목표 | 정식 SLA 없음 (프로토타입). 개발/시연 환경 상시 가동 |
| A2 | 관리자 오프라인 동작 | 네트워크 단절 시 로컬 캐시로 마지막 상태 표시 (§4.2) |
| A3 | 재연결 동기화 | 재연결 시 REST 전체 스냅샷 재조회로 갱신 (last-write-wins, FD Q9) |
| A4 | 고객 장바구니 보존 | localStorage 자동 저장 (새로고침·일시 단절에도 유지) |
| A5 | 데이터 정합성 | 모든 다중-쓰기 연산(주문 생성, 세션 종료)은 DB 트랜잭션 |
| A6 | 범위 밖 | 자동 페일오버, 다중 AZ, 백업/복구 자동화 — Operations/향후 |

---

## 4. 보안 (Security)

> Security Baseline extension은 **비활성(off)** — 프로토타입. 아래는 애플리케이션 필수 기본 보안.

| ID | 요구사항 | 결정 | 관련 Unit |
|----|---------|------|----------|
| SEC1 | 비밀번호 저장 | **bcrypt** 해싱 (관리자 + 테이블 비밀번호) | U1 Auth |
| SEC2 | 관리자 세션 | **JWT**, 만료 16시간, 서명 검증 | U1 Auth |
| SEC3 | 인가 | FastAPI Dependency guard로 관리자/세션 토큰 분리 검증 | U0/U1 |
| SEC4 | 입력 검증 | Pydantic 스키마로 전 요청 검증 (가격 범위, 필수 필드 등) | 전체 |
| SEC5 | 전송 보안 | 프로덕션 배포 시 HTTPS 필수 (개발은 HTTP) | 인프라 |
| SEC6 | 금액 위변조 방지 | 주문 금액은 서버가 메뉴 테이블 기준 재계산 (FD Q5) | U3 Order |
| SEC7 | 세션 격리 | TableSession.id로 주문 조회 필터 (한 테이블이 타 테이블 주문 조회 불가) | U3/U5 |
| — | 범위 밖 | 레이트리밋, 로그인 시도 제한, 감사로그, OAuth — Security Baseline off로 이연 |

---

## 5. 신뢰성 / 오류 처리 (Reliability)

| ID | 요구사항 | 결정 | 관련 Unit |
|----|---------|------|----------|
| R1 | 네트워크 재시도 | 안전/멱등 요청 + 주문 생성(멱등키)에 대해 최대 3회 자동 재시도 | U3/U7 |
| R2 | 중복 주문 방지 | 클라이언트 생성 idempotency-key로 서버측 중복 차단 (FD Q6) | U3 Order |
| R3 | 세션 종료 원자성 | 이력 복사 + 현재 주문 삭제 + 총액 리셋을 단일 트랜잭션 (FD Q3) | U5 Table |
| R4 | 주문 실패 UX | 재시도 소진 시 에러 표시 + 장바구니 유지 (§3.1.4) | U7 Frontend |
| R5 | SSE 재연결 | 연결 끊김 감지 → 자동 재연결 → 스냅샷 재조회 | U4/U7 |

---

## 6. 데이터 관리 (Data Management)

| ID | 요구사항 | 결정 |
|----|---------|------|
| D1 | 이력 보관 | OrderHistory 3개월 보관 (§4.4) |
| D2 | 세션 격리 | TableSession.id 기반 (§4.4) |
| D3 | 세션 만료 | 관리자 16시간(JWT). 테이블 세션은 관리자 수동 종료 기준 |
| D4 | 트랜잭션 | 정합성 필요 연산 전부 트랜잭션 처리 |
| D5 | 이력 정리 | 3개월 경과분 정리(배치/수동) — Operations 단계로 이연 |

---

## 7. 유지보수성 & 관측성 (Maintainability & Observability)

| ID | 요구사항 | 결정 |
|----|---------|------|
| M1 | 아키텍처 | 계층형 (Router → Service → Repository), 도메인 서비스 경계 |
| M2 | API 문서 | FastAPI OpenAPI 자동 생성 (/docs) |
| M3 | 로깅 | 구조적 로깅 stdout (Docker 로그 수집 전제) |
| M4 | 테스트 | Property-Based Testing 활성 — 주문/결제 정합성 불변식 검증 |
| M5 | 코드 품질 | 타입힌트 + Pydantic, 프론트 컴포넌트 모듈화 |
| — | 범위 밖 | 메트릭(Prometheus)/트레이싱/알림 — Operations 단계로 이연 |

---

## 8. 사용성 (Usability)

| ID | 요구사항 | 결정 |
|----|---------|------|
| U1 | 고객 UI | 태블릿 터치 친화, 카테고리 네비, 반응형 |
| U2 | 관리자 UI | 데스크톱 카드 그리드, 신규 주문 시각 강조(색상/애니메이션) |
| U3 | 접근성 | 기본 대비/폰트 크기 준수 (WCAG 전면 준수는 범위 밖) |
| U4 | 피드백 | 주문/세션 종료 등 주요 액션에 성공/실패 명시적 피드백 |

---

## 9. NFR ↔ Unit 커버리지 매트릭스

| Unit | 주요 NFR |
|------|---------|
| U0 Core/Shared | SEC3, SEC4, M1, A5 |
| U1 Auth | SEC1, SEC2, SEC3, D3 |
| U2 Menu | P2, P5 |
| U3 Order | P1, R1, R2, SEC6, SEC7 |
| U4 Realtime & Dashboard | P3, P4, A2, A3, R5, S3 |
| U5 Table & Session | R3, D1, D2, A5 |
| U6 Menu Management | SEC4 (검증), M2 |
| U7 Frontend | P5, R4, A4, U1-U4 |

---

**상태**: ✅ 완료 (requirements §4 근거, 전부 권장값)
**다음 단계**: NFR Design
