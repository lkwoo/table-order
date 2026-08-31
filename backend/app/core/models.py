"""U0 Core - 통합 도메인 모델 (9 엔티티, 단일 SQLAlchemy Base).

domain-entities.md 스키마를 SQLAlchemy 2.0 매핑으로 구현.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.types import GUID


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def uuid_col(primary_key: bool = False, **kw) -> Mapped[uuid.UUID]:
    return mapped_column(GUID(), primary_key=primary_key, default=_uuid if primary_key else None, **kw)


class OrderStatus(str, enum.Enum):
    대기중 = "대기중"
    준비중 = "준비중"
    완료 = "완료"


class SessionStatus(str, enum.Enum):
    active = "active"
    ended = "ended"


# 상태 전이표 (U4 R1): 단방향 전진만 허용
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.대기중: {OrderStatus.준비중, OrderStatus.완료},
    OrderStatus.준비중: {OrderStatus.완료},
    OrderStatus.완료: set(),
}


class Store(Base):
    __tablename__ = "stores"
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = (UniqueConstraint("store_id", "username", name="uq_admin_store_username"),)
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Table(Base):
    __tablename__ = "tables"
    __table_args__ = (UniqueConstraint("store_id", "table_number", name="uq_table_store_number"),)
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    table_number: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class TableSession(Base):
    __tablename__ = "table_sessions"
    __table_args__ = (Index("ix_session_table_status", "table_id", "status"),)
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)  # = 세션 격리 키
    table_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tables.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[SessionStatus] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class Menu(Base):
    __tablename__ = "menus"
    __table_args__ = (Index("ix_menu_store_cat_order", "store_id", "category_id", "display_order"),)
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("menu_categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # 소프트 삭제 플래그
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_order_idempotency"),
        UniqueConstraint("store_id", "order_number", name="uq_order_store_number"),
        Index("ix_order_store_table", "store_id", "table_id"),
        Index("ix_order_session", "session_id"),
    )
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    table_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tables.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("table_sessions.id"), nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 매장 스코프 일련번호
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.대기중)
    total_amount: Mapped[int] = mapped_column(Integer, default=0)  # 서버 계산
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    menu_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("menus.id"), nullable=False)
    menu_name: Mapped[str] = mapped_column(String(200), nullable=False)  # 스냅샷
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 스냅샷
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")


class OrderHistory(Base):
    __tablename__ = "order_history"
    __table_args__ = (Index("ix_history_table_archived", "table_id", "archived_at"),)
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    table_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tables.id"), nullable=False)
    original_session_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    final_status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    items: Mapped[list[OrderHistoryItem]] = relationship(
        back_populates="history", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderHistoryItem(Base):
    __tablename__ = "order_history_items"
    id: Mapped[uuid.UUID] = uuid_col(primary_key=True)
    history_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("order_history.id"), nullable=False)
    menu_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)

    history: Mapped[OrderHistory] = relationship(back_populates="items")
