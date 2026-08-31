"""U2 Menu - 고객 조회 스키마."""
import uuid

from pydantic import BaseModel


class MenuItemOut(BaseModel):
    id: uuid.UUID
    name: str
    price: int
    description: str | None = None
    image_url: str | None = None


class MenuCategoryOut(BaseModel):
    category_id: uuid.UUID
    category_name: str
    display_order: int
    menus: list[MenuItemOut]
