"""U1 Auth - 라우터."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.schemas import (
    AdminContextResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    TableContextResponse,
    TableLoginRequest,
    TableLoginResponse,
)
from app.core.db import get_db
from app.core.security import AdminContext, SessionContext, get_current_admin, get_current_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/admin-login", response_model=AdminLoginResponse)
def admin_login(body: AdminLoginRequest, db: Session = Depends(get_db)):
    return service.admin_login(db, body.store_id, body.username, body.password)


@router.get("/admin-verify", response_model=AdminContextResponse)
def admin_verify(ctx: AdminContext = Depends(get_current_admin)):
    return AdminContextResponse(admin_id=ctx.admin_id, store_id=ctx.store_id)


@router.post("/table-login", response_model=TableLoginResponse)
def table_login(body: TableLoginRequest, db: Session = Depends(get_db)):
    return service.table_login(db, body.store_id, body.table_number, body.password)


@router.get("/table-verify", response_model=TableContextResponse)
def table_verify(ctx: SessionContext = Depends(get_current_session)):
    return TableContextResponse(
        table_id=ctx.table_id,
        session_id=ctx.session_id,
        store_id=ctx.store_id,
        expires_at=ctx.expires_at,
    )
