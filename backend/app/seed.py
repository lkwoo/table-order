"""개발용 시드 데이터: 매장 1개, 관리자, 카테고리/메뉴 샘플.

멱등: 이미 매장이 있으면 아무것도 하지 않음.
고정 UUID를 사용해 프론트 개발 시 store_id를 알 수 있게 함.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.models import Admin, Menu, MenuCategory, Store
from app.core.security import hash_password

STORE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"

_CATEGORIES = [
    ("메인", 0, [
        ("김치찌개", 9000, "얼큰한 김치찌개", None),
        ("된장찌개", 8500, "구수한 된장찌개", None),
        ("제육볶음", 11000, "매콤한 제육볶음", None),
    ]),
    ("음료", 1, [
        ("콜라", 2000, "시원한 콜라", None),
        ("사이다", 2000, "청량한 사이다", None),
    ]),
    ("주류", 2, [
        ("소주", 5000, "국민 소주", None),
        ("맥주", 6000, "시원한 생맥주", None),
    ]),
]


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        exists = db.execute(select(Store).where(Store.id == STORE_ID)).scalar_one_or_none()
        if exists is not None:
            return
        store = Store(id=STORE_ID, name="테이블오더 데모 매장")
        db.add(store)
        db.add(
            Admin(
                store_id=STORE_ID,
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
            )
        )
        for cat_name, cat_order, items in _CATEGORIES:
            cat = MenuCategory(store_id=STORE_ID, name=cat_name, display_order=cat_order)
            db.add(cat)
            db.flush()
            for idx, (name, price, desc, img) in enumerate(items):
                db.add(
                    Menu(
                        store_id=STORE_ID,
                        category_id=cat.id,
                        name=name,
                        price=price,
                        description=desc,
                        image_url=img,
                        display_order=idx,
                        is_active=True,
                    )
                )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_if_empty()
    print(f"Seed complete. store_id={STORE_ID}, admin={ADMIN_USERNAME}/{ADMIN_PASSWORD}")
