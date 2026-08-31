# AI-DLC State Tracking

## Project Information
- **Project Name**: 테이블오더 (Table Order Service)
- **Project Type**: Greenfield
- **Start Date**: 2026-08-31T12:45:00Z
- **Current Stage**: OPERATIONS (Complete — placeholder) → AI-DLC WORKFLOW COMPLETE

## Workspace State
- **Existing Code**: No
- **Reverse Engineering Needed**: No
- **Workspace Root**: `/c/claude/aidlc-workshop/table-order`

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Stage Progress

### INCEPTION Phase
- [x] Workspace Detection: ✅ Complete
- [x] Reverse Engineering: N/A (Greenfield - Skipped)
- [x] Requirements Analysis: ✅ Complete
- [x] User Stories: ✅ Complete (24 stories: Customer 11, Admin 13; 2 personas, story matrix)
- [x] Workflow Planning: ✅ Complete
- [x] Application Design: ✅ Complete (approved 2026-08-31; 5 design docs)
- [x] Units Generation: ✅ Complete (approved 2026-08-31; 8 units, 3 docs)

### CONSTRUCTION Phase
- [x] Functional Design: ✅ Complete (8 units; approved 2026-08-31 via "이어서 진행" instruction)
- [x] NFR Requirements: ✅ Complete (project-level, requirements §4 근거; nfr-requirements.md + tech-stack-decisions.md)
- [x] NFR Design: ✅ Complete (nfr-design-patterns.md + logical-components.md; EventBroker/AuthGuard/UoW/cache 논리 컴포넌트)
- [x] Infrastructure Design: ✅ Complete (Docker Compose db+backend+frontend, 단일 워커 제약, 디렉터리 구조, shared-infrastructure)
- [x] Code Generation: ✅ Complete (approved 2026-08-31 "진행해줘"; 8 units — backend FastAPI + frontend React + Docker Compose; 13 tests pass incl. 7 PBT 불변식)
- [x] Build and Test: ✅ Complete (approved 2026-08-31 "진행해줘"; backend 17 pytest pass, ~85% coverage, 7 PBT + 4 integration). Frontend 빌드 완결(2026-08-31): Node 24.19.0 설치 → `npm run build` 성공, dist JS 198 kB/gzip 62.5 kB (tsconfig/@types/node 수정). Docker는 정적 검증만(런타임 미설치, CI/CD에서 실행).

### OPERATIONS Phase
- [x] Operations: ✅ Complete (Placeholder — approved 2026-08-31 "2"; AI-DLC 워크플로는 Build and Test 이후 종료. 배포/모니터링/장애대응은 Future Scope)

**🎉 AI-DLC WORKFLOW COMPLETE** — 8 units, INCEPTION → CONSTRUCTION 전 단계 완료, 백엔드 17 tests pass (85% cov). 프런트/Docker는 런타임 없는 환경으로 CI/CD에서 검증 예정.

## Extension Configuration

| Extension | Enabled | Decided At |
|-----------|---------|-----------|
| Security Baseline | No | Requirements Analysis |
| Resiliency Baseline | No | Requirements Analysis |
| Property-Based Testing | Yes | Requirements Analysis |

## Technology Stack Decisions
- **Backend**: Python/FastAPI
- **Frontend**: React
- **Database**: PostgreSQL
- **Real-time Communication**: Server-Sent Events (SSE)
- **Authentication**: JWT (16-hour session)
- **Development Environment**: Docker Compose

## Key Decisions
- **Project Classification**: Greenfield - Building from scratch
- **Scope**: MVP with core features only
- **Team Structure**: 1 Admin per Store (no multi-store/multi-role support)
- **Image Storage**: External URLs (no file upload)
- **Data Retention**: 3 months for order history
- **Next Action**: None — AI-DLC workflow complete. 실제 배포는 CI/CD(Node·Docker 환경)에서 프런트 빌드/컨테이너 검증 후 수행.
- **Git Policy**: Commit at every stage completion on `main`; push to origin at ≥3 commits (standing instruction from user, 2026-08-31)
