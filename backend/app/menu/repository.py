"""U2/U6 - Menu Repository (조회 캡슐화, 트랜잭션 미개시)."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Menu, MenuCategory


def list_categories(db: Session, store_id: uuid.UUID) -> list[MenuCategory]:
    return list(
        db.execute(
            select(MenuCategory)
            .where(MenuCategory.store_id == store_id)
            .order_by(MenuCategory.display_order)
        ).scalars()
    )


def list_menus(db: Session, store_id: uuid.UUID, active_only: bool) -> list[Menu]:
    stmt = select(Menu).where(Menu.store_id == store_id)
    if active_only:
        stmt = stmt.where(Menu.is_active.is_(True))
    stmt = stmt.order_by(Menu.category_id, Menu.display_order)
    return list(db.execute(stmt).scalars())


def get_menu(db: Session, store_id: uuid.UUID, menu_id: uuid.UUID) -> Menu | None:
    return db.execute(
        select(Menu).where(Menu.id == menu_id, Menu.store_id == store_id)
    ).scalar_one_or_none()
