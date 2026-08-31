# Infrastructure Design Plan - 테이블오더 서비스 (프로젝트 레벨)

**작성일**: 2026-08-31
**단계**: CONSTRUCTION - Infrastructure Design
**범위**: 논리 컴포넌트 → 실제 배포/실행 인프라 매핑

---

# PART 1: PLANNING - 체크리스트

## Step 1: 설계 산출물 분석 ✅
- [x] functional-design + nfr-design(logical-components) 검토

## Step 2: 결정 질문 답변 (PART 2) ✅
- [x] 모든 [Answer]: 태그 작성 (전부 권장)

## Step 3: 산출물 생성 ✅
- [x] `infrastructure-design/infrastructure-design.md`
- [x] `infrastructure-design/deployment-architecture.md`
- [x] `shared-infrastructure.md` (모놀리스 공용)

---

# PART 2: 인프라 결정 질문

## Q1. 배포 환경 (Deployment Environment)

배포 타깃은?

- **A) 로컬 Docker Compose (개발/시연). 클라우드 배포는 범위 밖(향후)** ⭐권장
  - requirements §2.3. 프로토타입 — AWS/Azure/GCP 미결정
- **B) 특정 클라우드(AWS 등) 즉시 타깃**

[Answer]: A

---

## Q2. 컴퓨트 (Compute)

백엔드 실행 방식은?

- **A) Docker 컨테이너 1개 (uvicorn, 단일 워커/프로세스 — 인메모리 EventBroker/캐시 일관성 위해)** ⭐권장
  - 멀티 워커 시 인메모리 상태 분산 문제 → 단일 워커. 부하 20-30 동시엔 충분
- **B) 멀티 워커 gunicorn + 외부 브로커**

[Answer]: A

---

## Q3. 스토리지 (Storage)

DB 실행/영속화는?

- **A) PostgreSQL 16 컨테이너 + named volume(데이터 영속), Alembic 마이그레이션** ⭐권장
- **B) 매니지드 DB(RDS 등)**

[Answer]: A

---

## Q4. 메시징 (Messaging)

이벤트 처리 인프라는?

- **A) 없음 — 인프로세스 EventBroker(asyncio) 사용** ⭐권장
- **B) 외부 브로커(Redis/RabbitMQ) 컨테이너 추가**

[Answer]: A

---

## Q5. 네트워킹 (Networking)

프론트/백엔드 노출 및 CORS는?

- **A) 개발: Vite dev 서버(프론트) + uvicorn(백엔드), CORS 허용. 프로덕션: nginx가 정적 프론트 서빙 + /api 리버스 프록시(단일 오리진)** ⭐권장
- **B) 별도 API Gateway 도입**

[Answer]: A

---

## Q6. 모니터링 (Monitoring)

관측성 인프라는?

- **A) 컨테이너 stdout 로그(docker compose logs) + FastAPI /health 헬스체크. 풀 관측성 스택은 Operations로 이연** ⭐권장
- **B) Prometheus/Grafana 스택 도입**

[Answer]: A

---

## Q7. 공용 인프라 / 격리 (Shared / Isolation)

멀티테넌시·리소스 격리는?

- **A) 단일 매장(1 Store) 기준 단일 배포. store_id로 데이터 스코핑(논리 격리). 멀티테넌시 인프라 격리는 범위 밖** ⭐권장
- **B) 매장별 인프라 격리**

[Answer]: A

---

## Q8. 환경 설정 / 시크릿 (Config & Secrets)

설정 관리 방식은?

- **A) .env 파일 + docker-compose 환경변수(JWT_SECRET, DATABASE_URL, JWT_EXP_HOURS=16). 시크릿 매니저는 범위 밖** ⭐권장
- **B) 외부 시크릿 매니저(Vault/SSM)**

[Answer]: A

---

**상태**: 답변 완료 (전부 권장) → 산출물 생성 완료
