"""테스트 데이터 팩토리."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.models import (
    Menu,
    MenuCategory,
    SessionStatus,
    Store,
    Table,
    TableSession,
)
from app.core.security import SessionContext, hash_password


def make_store(db: Session, name: str = "테스트매장") -> Store:
    store = Store(name=name)
    db.add(store)
    db.commit()
    return store


def make_category(db: Session, store_id: uuid.UUID, name: str = "메인", order: int = 0) -> MenuCategory:
    cat = MenuCategory(store_id=store_id, name=name, display_order=order)
    db.add(cat)
    db.commit()
    return cat


def make_menu(
    db: Session,
    store_id: uuid.UUID,
    category_id: uuid.UUID,
    name: str,
    price: int,
    order: int = 0,
    is_active: bool = True,
) -> Menu:
    menu = Menu(
        store_id=store_id,
        category_id=category_id,
        name=name,
        price=price,
        display_order=order,
        is_active=is_active,
    )
    db.add(menu)
    db.commit()
    return menu


def make_table(db: Session, store_id: uuid.UUID, number: str = "1", password: str = "1234") -> Table:
    table = Table(store_id=store_id, table_number=number, password_hash=hash_password(password))
    db.add(table)
    db.commit()
    return table


def make_session(db: Session, table: Table) -> TableSession:
    sess = TableSession(
        table_id=table.id,
        token=secrets.token_urlsafe(16),
        status=SessionStatus.active,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=16),
    )
    db.add(sess)
    db.commit()
    return sess


def session_ctx(store_id: uuid.UUID, table: Table, sess: TableSession) -> SessionContext:
    return SessionContext(
        session_id=sess.id,
        table_id=table.id,
        store_id=store_id,
        expires_at=sess.expires_at,
    )
