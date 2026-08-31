"""U3 Order - 주문 생성/조회 워크플로우 (C10, C11, C12).

핵심 규칙:
- R1 서버가 Menu.price 기준 total 재계산 (클라이언트 값 불신)
- R4 idempotency_key 중복 시 기존 주문 반환 (신규 생성 금지)
- R2/R3 세션 격리 (session_id 귀속/필터)
- R8 커밋 성공 후에만 OrderCreated 이벤트 발행
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.db import unit_of_work
from app.core.errors import unprocessable
from app.core.event_broker import Event, broker, dashboard_topic
from app.core.models import Menu, Order, OrderItem, OrderStatus
from app.core.security import SessionContext
from app.order import repository as repo


def _serialize(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "total_amount": order.total_amount,
        "items": [
            {
                "menu_id": it.menu_id,
                "menu_name": it.menu_name,
                "unit_price": it.unit_price,
                "quantity": it.quantity,
                "subtotal": it.subtotal,
            }
            for it in order.items
        ],
        "created_at": order.created_at,
    }


def create_order(ctx: SessionContext, idempotency_key: str, items_in: list) -> dict:
    """워크플로우 1: 주문 생성. 반환 dict + 신규 생성 여부(이벤트 발행용)."""
    published_event: Event | None = None
    with unit_of_work() as db:
        # 1. 멱등성 검사 (R4)
        existing = repo.get_by_idempotency_key(db, idempotency_key)
        if existing is not None:
            return _serialize(existing)

        # 3. 서버측 재검증 + 스냅샷 (R1, R7, R9)
        order_items: list[OrderItem] = []
        total = 0
        for item in items_in:
            menu = db.get(Menu, item.menu_id)
            if menu is None or not menu.is_active or menu.store_id != ctx.store_id:
                raise unprocessable("주문할 수 없는 메뉴가 포함되어 있습니다.")
            subtotal = menu.price * item.quantity  # 서버 단가 사용
            total += subtotal
            order_items.append(
                OrderItem(
                    menu_id=menu.id,
                    menu_name=menu.name,  # 스냅샷
                    unit_price=menu.price,  # 스냅샷
                    quantity=item.quantity,
                    subtotal=subtotal,
                )
            )

        # 4. order_number (Q2) + 5. total (Q5)
        order_number = repo.next_order_number(db, ctx.store_id)

        # 6. 저장 (session_id 귀속, R2)
        order = Order(
            store_id=ctx.store_id,
            table_id=ctx.table_id,
            session_id=ctx.session_id,
            order_number=order_number,
            status=OrderStatus.대기중,
            total_amount=total,
            idempotency_key=idempotency_key,
            items=order_items,
        )
        db.add(order)
        db.flush()
        result = _serialize(order)
        published_event = Event(
            type="order.created",
            data={
                "order_id": str(order.id),
                "table_id": str(order.table_id),
                "session_id": str(order.session_id),
                "order_number": order.order_number,
                "status": order.status.value,
                "total_amount": order.total_amount,
            },
        )
        store_id = ctx.store_id
    # 7. 커밋 후 이벤트 발행 (R8)
    if published_event is not None:
        broker.publish(dashboard_topic(store_id), published_event)
    return result


def list_current_orders(db: Session, ctx: SessionContext) -> list[dict]:
    """워크플로우 2: 현재 세션 주문 조회 (C11, C12 격리)."""
    orders = repo.list_by_session(db, ctx.session_id)
    return [_serialize(o) for o in orders]
