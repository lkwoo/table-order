"""U3 Order - Repository (조회 캡슐화)."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.models import Order, OrderStatus


def get_by_idempotency_key(db: Session, key: str) -> Order | None:
    return db.execute(select(Order).where(Order.idempotency_key == key)).scalar_one_or_none()


def next_order_number(db: Session, store_id: uuid.UUID) -> int:
    """매장 스코프 단조 증가 (Q2). 이력으로 이동한 주문 번호와도 연속되도록
    현재 주문 + 이력의 최대값 기준 +1."""
    from app.core.models import OrderHistory

    cur_max = db.execute(
        select(func.coalesce(func.max(Order.order_number), 0)).where(Order.store_id == store_id)
    ).scalar_one()
    hist_max = db.execute(
        select(func.coalesce(func.max(OrderHistory.order_number), 0)).where(
            OrderHistory.store_id == store_id
        )
    ).scalar_one()
    return max(cur_max, hist_max) + 1


def list_by_session(db: Session, session_id: uuid.UUID) -> list[Order]:
    """세션 격리 강제 (Q4/C12). 시간 역순."""
    return list(
        db.execute(
            select(Order).where(Order.session_id == session_id).order_by(Order.created_at.desc())
        ).scalars()
    )


def get_by_id(db: Session, store_id: uuid.UUID, order_id: uuid.UUID) -> Order | None:
    return db.execute(
        select(Order).where(Order.id == order_id, Order.store_id == store_id)
    ).scalar_one_or_none()
