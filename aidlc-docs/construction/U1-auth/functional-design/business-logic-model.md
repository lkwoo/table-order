# Business Logic Model - U1 Auth

**작성일**: 2026-08-31
**Unit**: U1 Auth | **스토리**: A1(관리자 로그인), C1(자동 로그인), C2(테이블 로그인)

---

## 워크플로우 1: 관리자 로그인 (A1)
```
입력: store_id, username, password
1. AdminRepository.get_by_credentials(store_id, username)
2. 없으면 → 401 (자격 오류, 존재 여부 노출 안 함)
3. bcrypt.verify(password, admin.password_hash)
4. 실패 → 401
5. 성공 → JWT 발급: payload{ admin_id, store_id, exp = now+16h }
6. 반환: { access_token, expires_at }
```

## 워크플로우 2: 관리자 토큰 검증 (자동 로그인/새로고침)
```
입력: Authorization: Bearer <jwt>
1. 서명 검증 + exp 검사
2. 만료/무효 → 401 (프론트는 로그인 화면으로)
3. 유효 → AdminContext{ admin_id, store_id }
```

## 워크플로우 3: 테이블 초기 로그인 (C2)
```
입력: table_number, password (+ store 식별)
1. TableRepository로 (store_id, table_number) 조회
2. 없으면/비번 불일치 → 401
3. active TableSession 확인:
   - active 세션 있으면 그 세션 사용
   - 없으면 → 새 TableSession 생성(token, expires=now+16h, status=active)
4. 반환: { session_token, table_id, session_id, expires_at }
   → 고객 태블릿 localStorage에 저장
```

## 워크플로우 4: 테이블 자동 로그인 (C1)
```
입력: localStorage의 session_token
1. verify_table_session(token): 서명/만료/status=active 검사
2. 유효 → 메뉴 화면 진입 (TableSessionContext 반환)
3. 만료/무효 → 초기 설정 화면으로 리다이렉트(재로그인 필요)
```

---

## 데이터 흐름
- 입력: 자격증명/토큰 → 출력: 토큰 또는 컨텍스트
- 지속성: Admin/Table 조회, TableSession 생성/조회 (U0 엔티티)
- 부작용: TableSession 생성(로그인 시)

## 통합 지점
- U0: AdminRepository, TableRepository, TableSessionRepository, 비밀번호 해싱, JWT 유틸
- 다른 Unit: AuthGuard 의존성으로 제공(U2~U6가 사용)

## 오류 시나리오
- 자격 오류 → 401 통일 메시지
- 세션 만료 → 401 + 재로그인 유도
- 네트워크 오류(로그인) → 클라이언트 3초 후 재시도 ×3 (C2 AC)
