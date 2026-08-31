# U1-auth — 코드 요약

관리자/테이블 인증 및 세션 발급.

## 생성 파일 (`backend/app/auth/`)
- `schemas.py` — AdminLogin/TableLogin 요청·응답, 컨텍스트 검증 응답.
- `service.py` — `admin_login`(자격 오류 시 존재 여부 미노출, R3), `table_login`(`_get_or_create_active_session`, 테이블당 active 세션 최대 1개, R5).
- `router.py` — 4개 엔드포인트: `POST /api/auth/admin-login`, `GET /api/auth/admin-verify`, `POST /api/auth/table-login`, `GET /api/auth/table-verify`.

## 스토리 / 규칙
- 관리자 JWT 16시간, 테이블 세션 16시간.
- R3: 로그인 실패는 항상 동일한 401(계정 열거 방지).
- R5: 만료된 active 세션은 ended 처리 후 신규 발급, 유효하면 재사용.

## 테스트 (`backend/tests/test_auth.py`)
- 비밀번호 해시 라운드트립(PBT), 로그인 성공/실패 비열거, active 세션 재사용, 오답 401.
