"""U6 Menu Management - 라우터 (관리자 JWT)."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import AdminContext, get_current_admin
from app.menu_mgmt import service
from app.menu_mgmt.schemas import (
    AdminMenuCategoryOut,
    AdminMenuOut,
    CategoryOut,
    MenuCreate,
    MenuUpdate,
    ReorderRequest,
)

router = APIRouter(prefix="/api/admin", tags=["menu-management"])


@router.get("/menus", response_model=list[AdminMenuCategoryOut])
def list_menus(ctx: AdminContext = Depends(get_current_admin), db: Session = Depends(get_db)):
    return service.list_admin_menus(db, ctx.store_id)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(ctx: AdminContext = Depends(get_current_admin), db: Session = Depends(get_db)):
    return service.list_categories(db, ctx.store_id)


@router.post("/menus", response_model=AdminMenuOut, status_code=201)
def create_menu(body: MenuCreate, ctx: AdminContext = Depends(get_current_admin)):
    return service.create_menu(ctx.store_id, body)


# reorder는 /{menu_id} 보다 먼저 선언 (경로 충돌 방지)
@router.patch("/menus/reorder")
def reorder(body: ReorderRequest, ctx: AdminContext = Depends(get_current_admin)):
    return service.reorder_menus(ctx.store_id, body.category_id, body.ordered_menu_ids)


@router.put("/menus/{menu_id}", response_model=AdminMenuOut)
def update_menu(menu_id: uuid.UUID, body: MenuUpdate, ctx: AdminContext = Depends(get_current_admin)):
    return service.update_menu(ctx.store_id, menu_id, body)


@router.delete("/menus/{menu_id}")
def delete_menu(menu_id: uuid.UUID, ctx: AdminContext = Depends(get_current_admin)):
    return service.soft_delete_menu(ctx.store_id, menu_id)
