# Build Instructions

## Prerequisites
- **Build Tools**: Python 3.12 (개발 검증은 3.11.9 로 수행), Node.js 20+, Docker / Docker Compose
- **Dependencies**: `backend/requirements.txt`, `frontend/package.json`
- **Environment Variables**: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` (`.env.example` 참조)
- **System Requirements**: 2GB+ RAM, 2GB+ 디스크

## Build Steps

### 1. Install Dependencies
```bash
# Backend
cd backend
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env     # 프로젝트 루트. 필요 시 JWT_SECRET 등 수정
```

### 3. Build All Units
```bash
# 전체 스택 (권장) — 루트에서
docker compose up --build

# 또는 개별 빌드
cd frontend && npm run build          # tsc + vite build → frontend/dist
cd ../backend && python -c "import app.main"   # 임포트/컴파일 확인
```

### 4. Verify Build Success
- **Backend**: `import app.main` 성공, `uvicorn app.main:app --workers 1` 기동 시 `/health` → `{"status":"ok"}`
- **Frontend**: `npm run build` 성공 시 `frontend/dist/` 생성 (프로덕션 정적 번들)
- **Docker**: `docker compose up` 후 db(5432)/backend(8000)/frontend(5173) 컨테이너 healthy
- **Common Warnings**: Git CRLF 경고(Windows, 무해), pytest-asyncio loop-scope Deprecation 경고(무해)

## Troubleshooting

### Build Fails with Dependency Errors
- **Cause**: 파이썬/노드 버전 불일치, 네트워크
- **Solution**: Python 3.12 및 Node 20 확인, `pip install --upgrade pip` 후 재설치

### Backend가 DB에 연결하지 못함
- **Cause**: `DATABASE_URL` 미설정 또는 db 컨테이너 미기동
- **Solution**: `docker compose up db` 로 DB 먼저 기동, healthcheck 통과 확인

### bcrypt 관련 오류
- **Cause**: bcrypt 72바이트 초과 입력
- **Solution**: 비밀번호는 애플리케이션 제약(4~10자) 내에서 사용
