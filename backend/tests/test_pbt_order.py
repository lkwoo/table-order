"""U3 Order PBT 불변식 (Hypothesis).

1. total_amount == Σ(unit_price × quantity)
2. 동일 idempotency_key N회 → 주문 1건
3. 세션 격리: 세션A 조회에 세션B 주문 없음
"""
from __future__ import annotations

import uuid

from hypothesis import given, settings
from hypothesis import strategies as st

from app.order import service as order_service
from app.order.schemas import OrderItemIn
from tests.factories import (
    make_category,
    make_menu,
    make_session,
    make_store,
    make_table,
    session_ctx,
)

_prices = st.integers(min_value=1000, max_value=100000)
_qtys = st.integers(min_value=1, max_value=99)


@settings(max_examples=40, deadline=None)
@given(
    specs=st.lists(st.tuples(_prices, _qtys), min_size=1, max_size=6),
)
def test_total_amount_invariant(db, specs):
    store = make_store(db)
    cat = make_category(db, store.id)
    table = make_table(db, store.id, number=str(uuid.uuid4())[:8])
    sess = make_session(db, table)
    ctx = session_ctx(store.id, table, sess)

    items = []
    expected = 0
    for i, (price, qty) in enumerate(specs):
        m = make_menu(db, store.id, cat.id, f"메뉴{i}", price, order=i)
        items.append(OrderItemIn(menu_id=m.id, quantity=qty))
        expected += price * qty

    result = order_service.create_order(ctx, f"key-{uuid.uuid4()}", items)
    assert result["total_amount"] == expected
    assert sum(it["subtotal"] for it in result["items"]) == expected


@settings(max_examples=20, deadline=None)
@given(n=st.integers(min_value=2, max_value=6))
def test_idempotency(db, n):
    store = make_store(db)
    cat = make_category(db, store.id)
    table = make_table(db, store.id, number=str(uuid.uuid4())[:8])
    sess = make_session(db, table)
    ctx = session_ctx(store.id, table, sess)
    m = make_menu(db, store.id, cat.id, "김치찌개", 9000)

    key = f"idem-{uuid.uuid4()}"
    results = [
        order_service.create_order(ctx, key, [OrderItemIn(menu_id=m.id, quantity=1)])
        for _ in range(n)
    ]
    # 모두 동일 주문 id
    ids = {r["id"] for r in results}
    assert len(ids) == 1

    from sqlalchemy import func, select

    from app.core.models import Order

    count = db.execute(
        select(func.count()).select_from(Order).where(Order.idempotency_key == key)
    ).scalar_one()
    assert count == 1


@settings(max_examples=20, deadline=None)
@given(a_qty=_qtys, b_qty=_qtys)
def test_session_isolation(db, a_qty, b_qty):
    store = make_store(db)
    cat = make_category(db, store.id)
    m = make_menu(db, store.id, cat.id, "메뉴", 5000)

    table = make_table(db, store.id, number=str(uuid.uuid4())[:8])
    sess_a = make_session(db, table)
    ctx_a = session_ctx(store.id, table, sess_a)
    order_service.create_order(ctx_a, f"a-{uuid.uuid4()}", [OrderItemIn(menu_id=m.id, quantity=a_qty)])

    table_b = make_table(db, store.id, number=str(uuid.uuid4())[:8])
    sess_b = make_session(db, table_b)
    ctx_b = session_ctx(store.id, table_b, sess_b)
    order_service.create_order(ctx_b, f"b-{uuid.uuid4()}", [OrderItemIn(menu_id=m.id, quantity=b_qty)])

    a_orders = order_service.list_current_orders(db, ctx_a)
    b_orders = order_service.list_current_orders(db, ctx_b)
    assert len(a_orders) == 1
    assert len(b_orders) == 1
    assert a_orders[0]["id"] != b_orders[0]["id"]
