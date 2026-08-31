"""U6 Menu Management - 스키마 (검증: name/price/category 필수, price 1,000~100,000)."""
import uuid

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    display_order: int


class AdminMenuOut(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    price: int
    description: str | None = None
    image_url: str | None = None
    display_order: int
    is_active: bool


class AdminMenuCategoryOut(BaseModel):
    category_id: uuid.UUID
    category_name: str
    display_order: int
    menus: list[AdminMenuOut]


class MenuCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: int
    category_id: uuid.UUID
    description: str | None = None
    image_url: str | None = None

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("메뉴명은 필수입니다.")
        return v

    @field_validator("price")
    @classmethod
    def _price_range(cls, v: int) -> int:
        if not (settings.price_min <= v <= settings.price_max):
            raise ValueError(f"가격은 {settings.price_min:,}~{settings.price_max:,}원 사이여야 합니다.")
        return v


class MenuUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: int
    category_id: uuid.UUID
    description: str | None = None
    image_url: str | None = None

    _trim_name = field_validator("name")(MenuCreate._trim_name.__func__)
    _price_range = field_validator("price")(MenuCreate._price_range.__func__)


class ReorderRequest(BaseModel):
    category_id: uuid.UUID
    ordered_menu_ids: list[uuid.UUID]
