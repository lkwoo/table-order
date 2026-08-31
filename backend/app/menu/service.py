"""U2 Menu - 고객 조회 워크플로우 (C3, C4)."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.menu import repository as repo


def list_menu_by_category(db: Session, store_id: uuid.UUID) -> list[dict]:
    """워크플로우 1: is_active=true 메뉴만, 카테고리별 그룹핑 (R1, R2)."""
    categories = repo.list_categories(db, store_id)
    menus = repo.list_menus(db, store_id, active_only=True)
    by_cat: dict[uuid.UUID, list] = {}
    for m in menus:
        by_cat.setdefault(m.category_id, []).append(m)
    result = []
    for c in categories:
        items = by_cat.get(c.id, [])
        result.append(
            {
                "category_id": c.id,
                "category_name": c.name,
                "display_order": c.display_order,
                "menus": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "price": m.price,
                        "description": m.description,
                        "image_url": m.image_url,
                    }
                    for m in items
                ],
            }
        )
    return result


def get_menu_detail(db: Session, store_id: uuid.UUID, menu_id: uuid.UUID) -> dict:
    """워크플로우 2: 상세. 비활성/없음 → 404."""
    m = repo.get_menu(db, store_id, menu_id)
    if m is None or not m.is_active:
        raise not_found("메뉴를 찾을 수 없습니다.")
    return {
        "id": m.id,
        "name": m.name,
        "price": m.price,
        "description": m.description,
        "image_url": m.image_url,
    }
