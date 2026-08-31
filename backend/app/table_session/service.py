"""U5 Table & Session - 테이블 설정 / 세션 종료(원자 TX) / 이력 조회.

핵심 규칙:
- R1 (store_id, table_number) 유일 → 409
- R2 세션 종료는 단일 트랜잭션 (이력 이동 + 현재 주문 삭제 + 새 세션) — 실패 시 전체 롤백
- R3 이력은 스냅샷 저장 (메뉴 변경/삭제 독립)
- R4 새 세션(새 id)으로 이전 주문 격리
"""
from __future__ import annotations

import secrets
import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import unit_of_work
from app.core.errors import conflict, not_found
from app.core.event_broker import Event, broker, dashboard_topic
from app.core.models import (
    Order,
    OrderHistory,
    OrderHistoryItem,
    SessionStatus,
    Table,
    TableSession,
)
from app.core.security import hash_password


def create_table(store_id: uuid.UUID, table_number: str, password: str) -> dict:
    """워크플로우 1: 테이블 초기 설정 (A5)."""
    with unit_of_work() as db:
        dup = db.execute(
            select(Table).where(Table.store_id == store_id, Table.table_number == table_number)
        ).scalar_one_or_none()
        if dup is not None:
            raise conflict("이미 존재하는 테이블 번호입니다.")
        now = datetime.now(timezone.utc)
        table = Table(store_id=store_id, table_number=table_number, password_hash=hash_password(password))
        db.add(table)
        db.flush()
        sess = TableSession(
            table_id=table.id,
            token=secrets.token_urlsafe(32),
            status=SessionStatus.active,
            expires_at=now + timedelta(hours=settings.session_exp_hours),
        )
        db.add(sess)
        db.flush()
        return {"table_id": table.id, "table_number": table.table_number, "session_id": sess.id}


def list_tables(db: Session, store_id: uuid.UUID) -> list[dict]:
    tables = db.execute(
        select(Table).where(Table.store_id == store_id).order_by(Table.table_number)
    ).scalars()
    return [{"table_id": t.id, "table_number": t.table_number} for t in tables]


def end_session(store_id: uuid.UUID, table_id: uuid.UUID) -> dict:
    """워크플로우 2: 세션 종료 — 단일 원자 트랜잭션 (A7, R2)."""
    now = datetime.now(timezone.utc)
    archived_count = 0
    with unit_of_work() as db:
        table = db.execute(
            select(Table).where(Table.id == table_id, Table.store_id == store_id)
        ).scalar_one_or_none()
        if table is None:
            raise not_found("테이블을 찾을 수 없습니다.")

        active = db.execute(
            select(TableSession).where(
                TableSession.table_id == table_id, TableSession.status == SessionStatus.active
            )
        ).scalar_one_or_none()

        if active is not None:
            orders = list(
                db.execute(select(Order).where(Order.session_id == active.id)).scalars()
            )
            # a. 스냅샷 이력화 (Q3)
            for o in orders:
                hist = OrderHistory(
                    store_id=o.store_id,
                    table_id=o.table_id,
                    original_session_id=o.session_id,
                    order_number=o.order_number,
                    final_status=o.status,
                    total_amount=o.total_amount,
                    ordered_at=o.created_at,
                    completed_at=o.updated_at if o.status.value == "완료" else None,
                    archived_at=now,
                    items=[
                        OrderHistoryItem(
                            menu_name=it.menu_name,
                            unit_price=it.unit_price,
                            quantity=it.quantity,
                            subtotal=it.subtotal,
                        )
                        for it in o.items
                    ],
                )
                db.add(hist)
                archived_count += 1
            # b. 현재 주문 삭제
            for o in orders:
                db.delete(o)
            # c. 기존 세션 ended
            active.status = SessionStatus.ended
            active.ended_at = now

        # d. 새 세션 생성 (새 id/token → 격리, R4)
        new_sess = TableSession(
            table_id=table_id,
            token=secrets.token_urlsafe(32),
            status=SessionStatus.active,
            expires_at=now + timedelta(hours=settings.session_exp_hours),
        )
        db.add(new_sess)
        db.flush()
    # 커밋 후 이벤트 (대시보드 총액 0 갱신)
    broker.publish(
        dashboard_topic(store_id),
        Event(type="session.ended", data={"table_id": str(table_id)}),
    )
    return {"table_id": table_id, "archived_count": archived_count}


def _date_range(filter_: str, from_: str | None, to_: str | None) -> tuple[datetime | None, datetime | None]:
    today = datetime.now(timezone.utc).date()
    if filter_ == "today":
        start = datetime.combine(today, time.min, tzinfo=timezone.utc)
        return start, start + timedelta(days=1)
    if filter_ == "yesterday":
        y = today - timedelta(days=1)
        start = datetime.combine(y, time.min, tzinfo=timezone.utc)
        return start, start + timedelta(days=1)
    if from_ or to_:
        start = datetime.combine(date.fromisoformat(from_), time.min, tzinfo=timezone.utc) if from_ else None
        end = (
            datetime.combine(date.fromisoformat(to_), time.min, tzinfo=timezone.utc) + timedelta(days=1)
            if to_
            else None
        )
        return start, end
    return None, None


def list_history(
    db: Session,
    store_id: uuid.UUID,
    table_id: uuid.UUID,
    filter_: str = "all",
    from_: str | None = None,
    to_: str | None = None,
) -> list[dict]:
    """워크플로우 3: 과거 이력 조회 (A8). 3개월 이내, 시간 역순."""
    retention_start = datetime.now(timezone.utc) - timedelta(days=settings.history_retention_days)
    stmt = select(OrderHistory).where(
        OrderHistory.store_id == store_id,
        OrderHistory.table_id == table_id,
        OrderHistory.archived_at >= retention_start,
    )
    start, end = _date_range(filter_, from_, to_)
    if start is not None:
        stmt = stmt.where(OrderHistory.ordered_at >= start)
    if end is not None:
        stmt = stmt.where(OrderHistory.ordered_at < end)
    stmt = stmt.order_by(OrderHistory.ordered_at.desc())
    rows = db.execute(stmt).scalars()
    return [
        {
            "order_number": h.order_number,
            "ordered_at": h.ordered_at,
            "completed_at": h.completed_at,
            "total_amount": h.total_amount,
            "items": [
                {
                    "menu_name": it.menu_name,
                    "unit_price": it.unit_price,
                    "quantity": it.quantity,
                    "subtotal": it.subtotal,
                }
                for it in h.items
            ],
        }
        for h in rows
    ]
