"""U6 Menu Management - CRUD + reorder (A9~A13)."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import unit_of_work
from app.core.errors import not_found, unprocessable
from app.core.models import Menu, MenuCategory
from app.menu import repository as repo


def list_admin_menus(db: Session, store_id: uuid.UUID) -> list[dict]:
    """워크플로우 1: 관리자 메뉴 조회 (is_active 포함 전체)."""
    categories = repo.list_categories(db, store_id)
    menus = repo.list_menus(db, store_id, active_only=False)
    by_cat: dict[uuid.UUID, list] = {}
    for m in menus:
        by_cat.setdefault(m.category_id, []).append(m)
    return [
        {
            "category_id": c.id,
            "category_name": c.name,
            "display_order": c.display_order,
            "menus": [_menu_dict(m) for m in by_cat.get(c.id, [])],
        }
        for c in categories
    ]


def list_categories(db: Session, store_id: uuid.UUID) -> list[dict]:
    return [
        {"id": c.id, "name": c.name, "display_order": c.display_order}
        for c in repo.list_categories(db, store_id)
    ]


def _menu_dict(m: Menu) -> dict:
    return {
        "id": m.id,
        "category_id": m.category_id,
        "name": m.name,
        "price": m.price,
        "description": m.description,
        "image_url": m.image_url,
        "display_order": m.display_order,
        "is_active": m.is_active,
    }


def _require_category(db: Session, store_id: uuid.UUID, category_id: uuid.UUID) -> MenuCategory:
    cat = db.execute(
        select(MenuCategory).where(MenuCategory.id == category_id, MenuCategory.store_id == store_id)
    ).scalar_one_or_none()
    if cat is None:
        raise unprocessable("존재하지 않는 카테고리입니다.")
    return cat


def create_menu(store_id: uuid.UUID, data) -> dict:
    """워크플로우 2: 등록. display_order = 카테고리 말미+1."""
    with unit_of_work() as db:
        _require_category(db, store_id, data.category_id)
        max_order = db.execute(
            select(func.coalesce(func.max(Menu.display_order), -1)).where(
                Menu.store_id == store_id, Menu.category_id == data.category_id
            )
        ).scalar_one()
        menu = Menu(
            store_id=store_id,
            category_id=data.category_id,
            name=data.name,
            price=data.price,
            description=(data.description or None),
            image_url=(data.image_url or None),
            display_order=max_order + 1,
            is_active=True,
        )
        db.add(menu)
        db.flush()
        return _menu_dict(menu)


def update_menu(store_id: uuid.UUID, menu_id: uuid.UUID, data) -> dict:
    """워크플로우 3: 수정."""
    with unit_of_work() as db:
        menu = repo.get_menu(db, store_id, menu_id)
        if menu is None:
            raise not_found("메뉴를 찾을 수 없습니다.")
        _require_category(db, store_id, data.category_id)
        menu.name = data.name
        menu.price = data.price
        menu.category_id = data.category_id
        menu.description = data.description or None
        menu.image_url = data.image_url or None
        db.flush()
        return _menu_dict(menu)


def soft_delete_menu(store_id: uuid.UUID, menu_id: uuid.UUID) -> dict:
    """워크플로우 4: 소프트 삭제 (is_active=false). 주문/이력 스냅샷 보존 (R3)."""
    with unit_of_work() as db:
        menu = repo.get_menu(db, store_id, menu_id)
        if menu is None:
            raise not_found("메뉴를 찾을 수 없습니다.")
        menu.is_active = False
        db.flush()
        return {"id": menu.id, "is_active": menu.is_active}


def reorder_menus(store_id: uuid.UUID, category_id: uuid.UUID, ordered_ids: list[uuid.UUID]) -> dict:
    """워크플로우 5: 카테고리 내 순서 일괄 갱신. 부분 적용 금지 (R5)."""
    with unit_of_work() as db:
        _require_category(db, store_id, category_id)
        menus = repo.list_menus(db, store_id, active_only=False)
        cat_menu_ids = {m.id for m in menus if m.category_id == category_id}
        if set(ordered_ids) != cat_menu_ids:
            raise unprocessable("순서 목록이 카테고리 메뉴와 일치하지 않습니다.")
        id_to_menu = {m.id: m for m in menus}
        for index, mid in enumerate(ordered_ids):
            id_to_menu[mid].display_order = index
        db.flush()
        return {"updated": len(ordered_ids)}
