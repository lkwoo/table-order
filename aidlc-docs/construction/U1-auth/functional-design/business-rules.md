# Business Rules - U1 Auth

**작성일**: 2026-08-31 | **Unit**: U1 Auth

---

## 인증 규칙
| # | 규칙 |
|---|------|
| R1 | 관리자 JWT 유효기간 = 16시간, 로그인 시마다 신규 발급 |
| R2 | 비밀번호는 bcrypt 해시로만 저장/비교. 평문 저장 금지 |
| R3 | 자격 오류 메시지는 "존재 여부"를 구분 노출하지 않음(계정 열거 방지) |
| R4 | 테이블 세션 토큰 유효기간 = 16시간, status=active 인 동안만 유효 |
| R5 | table당 active TableSession은 최대 1개 |
| R6 | 세션 만료/종료 시 해당 토큰으로 어떤 데이터도 접근 불가 |
| R7 | 테이블 비밀번호 4~10자리 |
| R8 | 모든 인증은 store_id 스코프. 타 매장 리소스 접근 시 403 |

## 상태/전이
- TableSession.status: active → ended (세션 종료 A7 또는 만료). 역전이 없음.

## 검증
- 로그인 입력 필수 필드 누락 → 422
- 만료 판단: `now >= expires_at` 이면 만료로 간주(자동 로그아웃)

## Property-Based Test 후보 (PBT 활성)
- 임의의 비밀번호 문자열에 대해 `verify(pw, hash(pw)) == true` 불변식
- 만료 시각 경계값(±1초)에서 검증 결과 일관성
