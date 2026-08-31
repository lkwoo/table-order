# Unit of Work Plan - 테이블오더 서비스

**작성일**: 2026-08-31
**단계**: INCEPTION - Units Generation
**목적**: 시스템을 관리 가능한 개발 단위(Unit of Work)로 분해하기 위한 계획 + 결정 질문

---

## 개요

Application Design에서 정의한 컴포넌트/서비스를 개발 단위로 그룹화합니다.
- 이 프로젝트는 **단일 배포 애플리케이션(모놀리식)** 전제입니다(FastAPI 백엔드 + React 프론트 + PostgreSQL, 인메모리 EventBroker 단일 인스턴스).
- 따라서 "Unit"은 **하나의 서비스 내 논리적 모듈**로 정의합니다(마이크로서비스 분리가 아님).

**컨텍스트**:
- 24개 User Stories (고객 11, 관리자 13)
- 도메인별 서비스 7개 + EventBroker
- 9개 엔티티

---

# PART 1: PLANNING - 체크리스트

## Step 1: 컨텍스트 로드 ✅
- [x] requirements.md / stories.md / application-design 산출물 분석

## Step 2: 결정 질문 답변 (아래 PART 2) ✅
- [x] 모든 [Answer]: 태그 작성 완료 (전부 A/권장, 모호성 없음)

## Step 3: 산출물 생성 (승인 후) ✅
- [x] `application-design/unit-of-work.md` — 단위 정의 및 책임 + 코드 조직 전략(Greenfield)
- [x] `application-design/unit-of-work-dependency.md` — 단위 의존성 매트릭스
- [x] `application-design/unit-of-work-story-map.md` — 스토리 ↔ 단위 매핑
- [x] 단위 경계/의존성 검증, 모든 스토리 배정 확인

---

# PART 2: 분해 결정 질문 (Decomposition Decisions)

각 `[Answer]:` 태그 뒤에 답변해주세요. 권장값(⭐)이 있으며 "권장"으로 일괄 진행 가능합니다.

---

## Q1. 배포 모델 (Technical / Code Organization)

시스템의 배포 단위를 어떻게 볼까요?

- **A) 모놀리식 단일 서비스 (내부 논리 모듈로 분해)** ⭐권장
  - 백엔드 1개 서비스 + 프론트 1개 앱. Unit = 논리 모듈. 프로토타입/현재 규모(10-20 테이블)에 적합
- **B) 마이크로서비스 (Unit별 독립 배포)**
  - 인메모리 EventBroker·단일 인스턴스 전제와 상충, 범위 초과

[Answer]: A

---

## Q2. 스토리 그룹핑 기준 (Story Grouping)

Unit(모듈)을 어떤 기준으로 묶을까요?

- **A) 비즈니스 도메인/역량 기준** ⭐권장
  - 인증, 메뉴, 주문, 테이블·세션, 실시간(대시보드/이벤트) 등 도메인 단위. Application Design 서비스 경계와 일치
- **B) Persona 기준 (고객 모듈 / 관리자 모듈 2개)**
- **C) 기술 계층 기준 (프론트/백/DB)**

[Answer]: A

---

## Q3. 프론트엔드 단위 취급 (Code Organization)

프론트엔드(React)를 별도 Unit으로 다룰까요?

- **A) 프론트엔드를 독립 Unit으로, 내부는 고객/관리자 모듈로 구분** ⭐권장
  - 백엔드 도메인 Unit들과 분리해 관리 (빌드/배포 단위가 다름)
- **B) 각 도메인 Unit에 프론트+백을 함께 포함 (풀스택 슬라이스)**

[Answer]: A

---

## Q4. 공유 리소스/횡단 요소 처리 (Dependencies)

인증 가드, EventBroker, DB 세션/공용 스키마 등 공유 요소를 어떻게 배치할까요?

- **A) 공용 "Shared/Core" Unit으로 분리** ⭐권장
  - AuthGuard, EventBroker, DB(모델/UoW), 공통 Validator/ApiClient 등을 공유 기반 Unit에 배치
- **B) 각 Unit에 중복 배치**

[Answer]: A

---

## Q5. 디렉터리 구조 (Code Organization, Greenfield)

코드 조직 구조 선호는? (모놀리식 가정)

- **A) 백엔드 도메인별 패키지 + 프론트 앱 분리** ⭐권장
  ```
  /backend
    /app
      /core        (설정, DB, 인증 가드, EventBroker)
      /auth  /menu  /order  /table  /dashboard   (도메인별: router+service+repository+schema)
      main.py
  /frontend
    /src
      /customer  /admin  /shared
  /docker-compose.yml
  ```
- **B) 계층별 최상위 폴더 (routers/ services/ repositories/ ...)**

[Answer]: A

---

## Q6. 개발 순서/우선순위 (Team Alignment)

Unit 개발 순서는 어떻게 정할까요? (1인/소규모 개발 가정)

- **A) 의존성 순서 + Sprint 배치 따름** ⭐권장
  - Core → 인증 → 메뉴/주문 → 실시간 → 테이블관리 → 메뉴관리. Sprint 1(MVP) 우선
- **B) 기타 (설명)**

[Answer]: A

---

# PART 3: 다음 지침

1. Q1~Q6의 모든 [Answer]: 태그에 답변해주세요 ("권장" 일괄 가능).
2. 답변 완료 후 알려주세요. 모호한 부분이 있으면 후속 질문을 드립니다.
3. 확정되면 Unit 산출물 3종(unit-of-work.md, unit-of-work-dependency.md, unit-of-work-story-map.md)을 생성합니다.

---

**작성일**: 2026-08-31
**상태**: 답변 완료 (전부 권장) → 산출물 생성 완료
