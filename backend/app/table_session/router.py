"""U5 Table & Session - 라우터 (관리자 JWT)."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import AdminContext, get_current_admin
from app.table_session import service
from app.table_session.schemas import (
    EndSessionResponse,
    HistoryOut,
    TableCreate,
    TableCreateResponse,
    TableOut,
)

router = APIRouter(prefix="/api/admin/tables", tags=["table-session"])


@router.post("", response_model=TableCreateResponse, status_code=201)
def create_table(body: TableCreate, ctx: AdminContext = Depends(get_current_admin)):
    return service.create_table(ctx.store_id, body.table_number, body.password)


@router.get("", response_model=list[TableOut])
def list_tables(ctx: AdminContext = Depends(get_current_admin), db: Session = Depends(get_db)):
    return service.list_tables(db, ctx.store_id)


@router.post("/{table_id}/end-session", response_model=EndSessionResponse)
def end_session(table_id: uuid.UUID, ctx: AdminContext = Depends(get_current_admin)):
    return service.end_session(ctx.store_id, table_id)


@router.get("/{table_id}/history", response_model=list[HistoryOut])
def list_history(
    table_id: uuid.UUID,
    filter: str = Query(default="all"),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    ctx: AdminContext = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return service.list_history(db, ctx.store_id, table_id, filter, from_, to)
