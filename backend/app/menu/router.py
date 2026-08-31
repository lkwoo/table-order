"""U2 Menu - 고객 조회 라우터 (세션 토큰 필요)."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import SessionContext, get_current_session
from app.menu import service
from app.menu.schemas import MenuCategoryOut, MenuItemOut

router = APIRouter(prefix="/api/menus", tags=["menu"])


@router.get("", response_model=list[MenuCategoryOut])
def list_menus(ctx: SessionContext = Depends(get_current_session), db: Session = Depends(get_db)):
    return service.list_menu_by_category(db, ctx.store_id)


@router.get("/{menu_id}", response_model=MenuItemOut)
def get_menu(
    menu_id: uuid.UUID,
    ctx: SessionContext = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    return service.get_menu_detail(db, ctx.store_id, menu_id)
