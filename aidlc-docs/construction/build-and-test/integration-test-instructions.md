# Integration Test Instructions

## Purpose
유닛 간 상호작용을 HTTP 계층에서 검증한다. FastAPI `TestClient` 로 앱을
SQLite in-memory(StaticPool) 로 기동하고 실제 라우터/의존성/서비스/리포지토리를
end-to-end 로 통과시킨다. (`tests/test_integration_api.py`)

## Test Scenarios

### Scenario 1: 관리자 인증 → 테이블 관리 (U1 → U5)
- **Description**: 관리자 로그인 후 JWT 로 테이블 생성
- **Steps**: `POST /api/auth/admin-login` → Bearer 토큰 → `POST /api/admin/tables`
- **Expected**: 201, 테이블 생성

### Scenario 2: 테이블 로그인 → 메뉴 조회 → 주문 (U1 → U2 → U3)
- **Description**: 세션 토큰 발급 후 메뉴 조회, 주문 생성 시 서버 금액 재계산
- **Steps**: `POST /api/auth/table-login` → `X-Session-Token` → `GET /api/menus` → `POST /api/orders`
- **Expected**: `total_amount == Σ(price×qty)`

### Scenario 3: 대시보드 집계 + 상태 전이 (U3 → U4)
- **Description**: 주문이 대시보드 총액에 반영, 상태 단방향 전이 검증
- **Steps**: `GET /api/admin/dashboard` (총액 일치) → `PATCH .../status` 준비중(200) → 대기중(409)
- **Expected**: 역방향 전이는 409 거부

### Scenario 4: 인증 가드
- **Description**: 토큰 없는 보호 라우트 접근 거부, 잘못된 비밀번호 401
- **Expected**: `GET /api/admin/dashboard`(토큰 없음) → 401/403, 오답 로그인 → 401

## Setup & Run
```bash
cd backend
source .venv/Scripts/activate
python -m pytest tests/test_integration_api.py -q
```
- 별도 DB/서비스 기동 불필요 (in-memory SQLite, 앱 lifespan 이 스키마 생성 + 시드).
- **Expected**: 4 passed.

## Cleanup
- 픽스처 종료 시 `Base.metadata.drop_all` 로 자동 정리 (외부 리소스 없음).

## Docker 기반 수동 통합 확인 (선택)
```bash
docker compose up --build
# http://localhost:5173 (프런트) → 테이블 로그인/주문
# http://localhost:8000/health → 헬스체크
```
