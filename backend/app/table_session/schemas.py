"""U5 Table & Session - 스키마."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TableCreate(BaseModel):
    table_number: str = Field(min_length=1, max_length=50)
    password: str

    @field_validator("password")
    @classmethod
    def _pw_len(cls, v: str) -> str:
        if not (4 <= len(v) <= 10):  # 테이블 비밀번호 4~10자리 (R7)
            raise ValueError("비밀번호는 4~10자리여야 합니다.")
        return v

    @field_validator("table_number")
    @classmethod
    def _trim(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("테이블 번호는 필수입니다.")
        return v


class TableCreateResponse(BaseModel):
    table_id: uuid.UUID
    table_number: str
    session_id: uuid.UUID


class TableOut(BaseModel):
    table_id: uuid.UUID
    table_number: str


class EndSessionResponse(BaseModel):
    table_id: uuid.UUID
    archived_count: int


class HistoryItemOut(BaseModel):
    menu_name: str
    unit_price: int
    quantity: int
    subtotal: int


class HistoryOut(BaseModel):
    order_number: int
    ordered_at: datetime
    completed_at: datetime | None
    total_amount: int
    items: list[HistoryItemOut]
