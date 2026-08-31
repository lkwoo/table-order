"""U3 Order - 스키마."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.models import OrderStatus


class OrderItemIn(BaseModel):
    menu_id: uuid.UUID
    quantity: int = Field(ge=settings.quantity_min, le=settings.quantity_max)


class OrderCreate(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=100)
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    menu_id: uuid.UUID
    menu_name: str
    unit_price: int
    quantity: int
    subtotal: int


class OrderOut(BaseModel):
    id: uuid.UUID
    order_number: int
    status: OrderStatus
    total_amount: int
    items: list[OrderItemOut]
    created_at: datetime
