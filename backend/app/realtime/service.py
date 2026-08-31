"""U4 Realtime & Dashboard - 대시보드/상태변경/삭제 (A2, A3, A4, A6).

- R1 상태 전이 단방향 (ALLOWED_TRANSITIONS), 위반 409
- R2/R7 커밋 후 이벤트 발행, 대시보드 총액 = 미종료 주문 합
- R5 삭제 시 총액 재계산
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import unit_of_work
from app.core.errors import conflict, not_found
from app.core.event_broker import Event, broker, dashboard_topic, session_topic
from app.core.models import (
    ALLOWED_TRANSITIONS,
    Order,
    OrderStatus,
    SessionStatus,
    Table,
    TableSession,
)


def _order_out(o: Order) -> dict:
    return {
        "id": o.id,
        "order_number": o.order_number,
        "status": o.status,
        "total_amount": o.total_amount,
        "items": [
            {
                "menu_name": it.menu_name,
                "unit_price": it.unit_price,
                "quantity": it.quantity,
                "subtotal": it.subtotal,
            }
            for it in o.items
        ],
        "created_at": o.created_at,
    }


def _summary(o: Order) -> str:
    if not o.items:
        return "(항목 없음)"
    first = o.items[0].menu_name
    rest = len(o.items) - 1
    return f"{first} 외 {rest}건" if rest > 0 else first


def get_dashboard(db: Session, store_id: uuid.UUID) -> list[dict]:
    """워크플로우 1: 대시보드 데이터 (A2). 테이블별 active 세션 현재 주문 집계."""
    tables = list(
        db.execute(select(Table).where(Table.store_id == store_id).order_by(Table.table_number)).scalars()
    )
    cards = []
    for t in tables:
        active = db.execute(
            select(TableSession).where(
                TableSession.table_id == t.id, TableSession.status == SessionStatus.active
            )
        ).scalar_one_or_none()
        orders: list[Order] = []
        if active is not None:
            orders = list(
                db.execute(
                    select(Order).where(Order.session_id == active.id).order_by(Order.created_at.desc())
                ).scalars()
            )
        total = sum(o.total_amount for o in orders)  # R7: 미종료 주문 합
        cards.append(
            {
                "table_id": t.id,
                "table_number": t.table_number,
                "total_amount": total,
                "recent_orders": [
                    {"order_number": o.order_number, "status": o.status, "summary": _summary(o)}
                    for o in orders[:3]
                ],
                "has_new": False,
            }
        )
    return cards


def get_table_orders(db: Session, store_id: uuid.UUID, table_id: uuid.UUID) -> list[dict]:
    """워크플로우 2: 테이블 상세 주문 (A3). active 세션 전체 주문."""
    active = db.execute(
        select(TableSession)
        .join(Table, Table.id == TableSession.table_id)
        .where(
            TableSession.table_id == table_id,
            Table.store_id == store_id,
            TableSession.status == SessionStatus.active,
        )
    ).scalar_one_or_none()
    if active is None:
        return []
    orders = db.execute(
        select(Order).where(Order.session_id == active.id).order_by(Order.created_at.desc())
    ).scalars()
    return [_order_out(o) for o in orders]


def update_status(store_id: uuid.UUID, order_id: uuid.UUID, new_status: OrderStatus) -> dict:
    """워크플로우 3: 상태 변경 (A4). 단방향 전이 검증."""
    result: dict = {}
    event_targets: list[tuple[str, Event]] = []
    with unit_of_work() as db:
        order = db.execute(
            select(Order).where(Order.id == order_id, Order.store_id == store_id)
        ).scalar_one_or_none()
        if order is None:
            raise not_found("주문을 찾을 수 없습니다.")
        if new_status != order.status and new_status not in ALLOWED_TRANSITIONS[order.status]:
            raise conflict(f"'{order.status.value}' → '{new_status.value}' 상태 변경은 허용되지 않습니다.")
        order.status = new_status
        db.flush()
        result = _order_out(order)
        evt = Event(
            type="order.status_changed",
            data={
                "order_id": str(order.id),
                "session_id": str(order.session_id),
                "table_id": str(order.table_id),
                "status": new_status.value,
            },
        )
        event_targets = [
            (dashboard_topic(store_id), evt),
            (session_topic(order.session_id), evt),
        ]
    for topic, evt in event_targets:
        broker.publish(topic, evt)
    return result


def delete_order(store_id: uuid.UUID, order_id: uuid.UUID) -> dict:
    """워크플로우 4: 주문 삭제 (A6). 삭제 후 테이블 총액 재계산."""
    payload: dict = {}
    event_targets: list[tuple[str, Event]] = []
    with unit_of_work() as db:
        order = db.execute(
            select(Order).where(Order.id == order_id, Order.store_id == store_id)
        ).scalar_one_or_none()
        if order is None:
            raise not_found("주문을 찾을 수 없습니다.")
        session_id = order.session_id
        table_id = order.table_id
        db.delete(order)
        db.flush()
        # 총액 재계산 (R5)
        remaining = db.execute(select(Order).where(Order.session_id == session_id)).scalars()
        table_total = sum(o.total_amount for o in remaining)
        payload = {"table_id": table_id, "table_total": table_total}
        evt = Event(
            type="order.deleted",
            data={
                "order_id": str(order_id),
                "session_id": str(session_id),
                "table_id": str(table_id),
                "table_total": table_total,
            },
        )
        event_targets = [
            (dashboard_topic(store_id), evt),
            (session_topic(session_id), evt),
        ]
    for topic, evt in event_targets:
        broker.publish(topic, evt)
    return payload
