"""U1 Auth - Pydantic 스키마."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    store_id: uuid.UUID
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    store_id: uuid.UUID
    admin_id: uuid.UUID


class AdminContextResponse(BaseModel):
    admin_id: uuid.UUID
    store_id: uuid.UUID


class TableLoginRequest(BaseModel):
    store_id: uuid.UUID
    table_number: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TableLoginResponse(BaseModel):
    session_token: str
    table_id: uuid.UUID
    session_id: uuid.UUID
    expires_at: datetime


class TableContextResponse(BaseModel):
    table_id: uuid.UUID
    session_id: uuid.UUID
    store_id: uuid.UUID
    expires_at: datetime
