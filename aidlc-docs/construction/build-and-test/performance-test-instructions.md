# Performance Test Instructions

## Purpose
NFR 요구사항(requirements §4, nfr-requirements.md) 대비 성능을 검증한다.
MVP 규모(단일 매장, 10~20 테이블, 동시 20~30 세션)이므로 경량 부하 테스트로 충분하다.

## Performance Requirements (근거: NFR Requirements)
- **주문 생성 응답**: p95 < 1s
- **메뉴 로드**: < 2s
- **SSE 반영 지연**: < 2s
- **동시 사용자**: 20~30 세션
- **에러율**: < 1%

## Setup Performance Test Environment
```bash
docker compose up --build        # 단일 backend 워커(인메모리 EventBroker 제약)
export API_URL=http://localhost:8000
```

## Run Performance Tests

### 1. Load Test (예: k6)
```bash
# 예시 스크립트: 30 VU, 1분, 메뉴 조회 + 주문 생성
k6 run --vus 30 --duration 60s perf/order-flow.js
```
> 참고: 부하 스크립트(`perf/*.js`)는 본 MVP 범위에서 미작성. 위 명령은 템플릿.
> 대안으로 `hey`, `locust`, `ab` 사용 가능.

### 2. Stress Test
```bash
# VU 를 점진 증가시켜 한계 관찰 (단일 워커이므로 CPU-bound 지점 확인)
k6 run --vus 100 --duration 120s perf/order-flow.js
```

### 3. Analyze Results
- **Response Time**: p95 측정값 vs < 1s(주문) / < 2s(메뉴)
- **Throughput**: req/s
- **Error Rate**: < 1%
- **Bottlenecks**: 단일 uvicorn 워커, SQLite→PostgreSQL 전환, DB 인덱스(domain-entities.md) 활용도

## Optimization
성능 미달 시:
1. DB 인덱스/쿼리 점검 (N+1 회피, `session_id`/`store_id` 인덱스)
2. 메뉴 인메모리 캐시(TTL) 적용 여부 확인 (nfr-design-patterns.md)
3. 수직 확장(단일 워커 제약 유지) 또는 Operations 단계에서 외부 브로커 도입 검토

## Status
- **본 단계**: 자동 부하 테스트 미실행 (MVP 범위). 요구사항/설계에 성능 목표와 절차만 정의.
- 실제 부하 측정은 Operations(배포) 단계에서 실환경 대상으로 수행 권장.
