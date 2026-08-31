"""테이블오더 서비스 - FastAPI 앱 진입점.

계층: Router → Service → Repository (U0 M1).
단일 워커로 실행 (인메모리 EventBroker/캐시 일관성 — shared-infrastructure.md).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.menu.router import router as menu_router
from app.menu_mgmt.router import router as menu_mgmt_router
from app.order.router import router as order_router
from app.realtime.router import router as realtime_router
from app.table_session.router import router as table_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # 프로토타입: 앱 기동 시 스키마 생성 + 시드 (Alembic도 제공하나 개발 편의)
    from app.core.db import engine
    from app.core.models import Base

    Base.metadata.create_all(bind=engine)
    from app.seed import seed_if_empty

    seed_if_empty()
    yield


app = FastAPI(title="테이블오더 서비스 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(menu_router)
app.include_router(order_router)
app.include_router(realtime_router)
app.include_router(table_router)
app.include_router(menu_mgmt_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
