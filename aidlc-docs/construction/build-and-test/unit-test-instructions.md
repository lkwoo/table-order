# Unit Test Execution

## Run Unit Tests

### 1. Execute All Unit Tests
```bash
cd backend
source .venv/Scripts/activate
python -m pytest -q
# 커버리지 포함:
python -m pytest -q --cov=app --cov-report=term-missing
```

### 2. Review Test Results
- **Expected**: 17 tests pass, 0 failures
- **Test Coverage**: 라인 커버리지 ~85% (핵심 도메인 서비스/모델 위주)
- **Test Report**: 콘솔 출력 (`--cov-report=html` 로 `htmlcov/` 생성 가능)

### 테스트 파일 구성
- `tests/test_pbt_order.py` — 주문 총액/idempotency/세션 격리 (Hypothesis PBT)
- `tests/test_pbt_session.py` — 세션 종료 합계 보존 (PBT)
- `tests/test_transitions_and_menu.py` — 상태 전이 거부 · reorder 연속성 · 소프트삭제 스냅샷 (PBT + 규칙)
- `tests/test_auth.py` — bcrypt 라운드트립 · 로그인 비열거 · active 세션 재사용 (PBT + 규칙)
- `tests/test_integration_api.py` — HTTP 계층 통합 (아래 통합 테스트 문서 참조)

### 속성 기반 테스트(PBT) — 7개 불변식
1. `total_amount == Σ(unit_price × quantity)`
2. 동일 idempotency-key N회 → 주문 1건
3. 세션 격리
4. 세션 종료 시 합계 보존
5. `완료` → 이전 상태 전이 거부
6. reorder 후 `display_order` 0..n-1 연속·유일
7. 소프트 삭제 메뉴는 고객 조회 제외, 스냅샷 유지

### 3. Fix Failing Tests
실패 시:
1. 콘솔의 falsifying example(Hypothesis 반례) 확인
2. 서비스 계층 로직 수정
3. `python -m pytest tests/<file>::<test>` 로 재실행
