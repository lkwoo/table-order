"""U5 세션 종료 PBT 불변식.

4. 종료 전 현재 주문 합계 == 이력에 추가된 합계, 종료 후 현재 주문 0
"""
from __future__ import annotations

import uuid

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from app.core.models import Order, OrderHistory, SessionStatus, TableSession
from app.order import service as order_service
from app.order.schemas import OrderItemIn
from app.table_session import service as ts_service
from tests.factories import make_category, make_menu, make_session, make_store, make_table, session_ctx


@settings(max_examples=25, deadline=None)
@given(qtys=st.lists(st.integers(min_value=1, max_value=20), min_size=0, max_size=5))
def test_session_end_sum_conservation(db, qtys):
    store = make_store(db)
    cat = make_category(db, store.id)
    m = make_menu(db, store.id, cat.id, "메뉴", 3000)
    table = make_table(db, store.id, number=str(uuid.uuid4())[:8])
    sess = make_session(db, table)
    ctx = session_ctx(store.id, table, sess)

    total_before = 0
    for q in qtys:
        r = order_service.create_order(ctx, f"k-{uuid.uuid4()}", [OrderItemIn(menu_id=m.id, quantity=q)])
        total_before += r["total_amount"]

    ts_service.end_session(store.id, table.id)

    db.expire_all()  # 다른 세션(unit_of_work) 커밋 결과를 재조회

    # 종료 후 현재 주문 0
    current = db.execute(
        select(Order).join(TableSession, TableSession.id == Order.session_id)
    ).scalars().all()
    active_orders = [o for o in current]
    # 현재 주문(어느 세션이든)에 이 테이블 주문 없음
    assert all(o.table_id != table.id for o in active_orders)

    # 이력 합계 == 종료 전 합계
    hist = db.execute(select(OrderHistory).where(OrderHistory.table_id == table.id)).scalars().all()
    total_archived = sum(h.total_amount for h in hist)
    assert total_archived == total_before
    assert len(hist) == len(qtys)

    # 새 active 세션이 생성되고 이전 세션은 ended
    sessions = db.execute(select(TableSession).where(TableSession.table_id == table.id)).scalars().all()
    active = [s for s in sessions if s.status == SessionStatus.active]
    assert len(active) == 1
    assert active[0].id != sess.id  # 새 세션(격리)
