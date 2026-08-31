# AI-DLC State Tracking

## Project Information
- **Project Name**: 테이블오더 (Table Order Service)
- **Project Type**: Greenfield
- **Start Date**: 2026-08-31T12:45:00Z
- **Current Stage**: CONSTRUCTION - NFR Design (Complete) → Infrastructure Design in progress

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
- [ ] Infrastructure Design: EXECUTE (in progress)
- [ ] Code Generation: EXECUTE
- [ ] Build and Test: EXECUTE

### OPERATIONS Phase
- [ ] Operations: PLACEHOLDER (Future)

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
- **Next Action**: Await Functional Design approval, then proceed to NFR Requirements
- **Git Policy**: Commit at every stage completion on `main`; push to origin at ≥3 commits (standing instruction from user, 2026-08-31)
