"""U4 Realtime & Dashboard - 라우터 (관리자 대시보드/주문 + SSE 스트림)."""
from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.event_broker import broker, dashboard_topic, session_topic
from app.core.security import (
    AdminContext,
    SessionContext,
    get_current_admin,
    get_current_session,
)
from app.realtime import service
from app.realtime.schemas import (
    AdminOrderOut,
    DeleteResult,
    StatusUpdate,
    TableCardOut,
)

router = APIRouter(tags=["realtime"])

# 하트비트 간격(초) — 프록시 타임아웃 방지
_HEARTBEAT = 20


# ---- 관리자 대시보드 REST (A2/A3/A4/A6) ----
@router.get("/api/admin/dashboard", response_model=list[TableCardOut])
def dashboard(ctx: AdminContext = Depends(get_current_admin), db: Session = Depends(get_db)):
    return service.get_dashboard(db, ctx.store_id)


@router.get("/api/admin/tables/{table_id}/orders", response_model=list[AdminOrderOut])
def table_orders(
    table_id: uuid.UUID,
    ctx: AdminContext = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return service.get_table_orders(db, ctx.store_id, table_id)


@router.patch("/api/admin/orders/{order_id}/status", response_model=AdminOrderOut)
def update_status(order_id: uuid.UUID, body: StatusUpdate, ctx: AdminContext = Depends(get_current_admin)):
    return service.update_status(ctx.store_id, order_id, body.status)


@router.delete("/api/admin/orders/{order_id}", response_model=DeleteResult)
def delete_order(order_id: uuid.UUID, ctx: AdminContext = Depends(get_current_admin)):
    return service.delete_order(ctx.store_id, order_id)


# ---- SSE 스트림 (워크플로우 5) ----
async def _event_stream(request: Request, topic: str) -> AsyncIterator[str]:
    sub = broker.subscribe(topic)
    try:
        # 최초 연결 확인용 코멘트
        yield ": connected\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(sub.queue.get(), timeout=_HEARTBEAT)
                yield f"event: {event.type}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"  # keep-alive
    finally:
        broker.unsubscribe(sub)


@router.get("/api/sse/dashboard")
async def sse_dashboard(request: Request, ctx: AdminContext = Depends(get_current_admin)):
    """관리자 대시보드 SSE: 매장 전체 이벤트 (R4)."""
    return StreamingResponse(
        _event_stream(request, dashboard_topic(ctx.store_id)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/sse/orders")
async def sse_orders(request: Request, ctx: SessionContext = Depends(get_current_session)):
    """고객 주문내역 SSE: 자기 세션 이벤트만 (R3 격리)."""
    return StreamingResponse(
        _event_stream(request, session_topic(ctx.session_id)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
