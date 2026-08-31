"""U4 Realtime & Dashboard - 스키마."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.models import OrderStatus


class RecentOrderOut(BaseModel):
    order_number: int
    status: OrderStatus
    summary: str  # "김치찌개 외 2건"


class TableCardOut(BaseModel):
    table_id: uuid.UUID
    table_number: str
    total_amount: int
    recent_orders: list[RecentOrderOut]
    has_new: bool = False


class OrderItemOut(BaseModel):
    menu_name: str
    unit_price: int
    quantity: int
    subtotal: int


class AdminOrderOut(BaseModel):
    id: uuid.UUID
    order_number: int
    status: OrderStatus
    total_amount: int
    items: list[OrderItemOut]
    created_at: datetime


class StatusUpdate(BaseModel):
    status: OrderStatus


class DeleteResult(BaseModel):
    table_id: uuid.UUID
    table_total: int
