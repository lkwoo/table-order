"""U4 상태 전이 + U6 메뉴 관리 PBT/규칙 검증.

5. 완료 → 이전 상태 전이 항상 거부
6. reorder 후 display_order 0..n-1 연속·유일
7. 소프트 삭제 메뉴는 고객 조회 제외, 기존 스냅샷 유지
"""
from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.models import ALLOWED_TRANSITIONS, OrderStatus
from app.menu import service as menu_service
from app.menu_mgmt import service as mgmt_service
from app.order import service as order_service
from app.order.schemas import OrderItemIn
from app.realtime import service as rt_service
from tests.factories import make_category, make_menu, make_session, make_store, make_table, session_ctx


def test_transition_table_forward_only():
    # 완료는 어떤 상태로도 갈 수 없음
    assert ALLOWED_TRANSITIONS[OrderStatus.완료] == set()
    # 준비중 → 대기중 불가
    assert OrderStatus.대기중 not in ALLOWED_TRANSITIONS[OrderStatus.준비중]


@settings(max_examples=15, deadline=None)
@given(target=st.sampled_from([OrderStatus.대기중, OrderStatus.준비중]))
def test_completed_cannot_revert(db, target):
    store = make_store(db)
    cat = make_category(db, store.id)
    m = make_menu(db, store.id, cat.id, "메뉴", 5000)
    table = make_table(db, store.id, number=str(uuid.uuid4())[:8])
    sess = make_session(db, table)
    ctx = session_ctx(store.id, table, sess)
    r = order_service.create_order(ctx, f"k-{uuid.uuid4()}", [OrderItemIn(menu_id=m.id, quantity=1)])
    order_id = r["id"]

    rt_service.update_status(store.id, order_id, OrderStatus.완료)
    with pytest.raises(HTTPException) as exc:
        rt_service.update_status(store.id, order_id, target)
    assert exc.value.status_code == 409


@settings(max_examples=20, deadline=None)
@given(n=st.integers(min_value=2, max_value=6), seed=st.randoms(use_true_random=True))
def test_reorder_continuity(db, n, seed):
    store = make_store(db)
    cat = make_category(db, store.id)
    menus = [make_menu(db, store.id, cat.id, f"메뉴{i}", 3000 + i, order=i) for i in range(n)]
    ids = [m.id for m in menus]
    shuffled = ids[:]
    seed.shuffle(shuffled)

    mgmt_service.reorder_menus(store.id, cat.id, shuffled)

    db.expire_all()  # 다른 세션(unit_of_work) 커밋 결과를 재조회
    refreshed = mgmt_service.list_admin_menus(db, store.id)
    cat_menus = refreshed[0]["menus"]
    orders = sorted(m["display_order"] for m in cat_menus)
    assert orders == list(range(n))  # 연속·유일
    # 순서가 요청대로 반영
    by_id = {m["id"]: m["display_order"] for m in cat_menus}
    for idx, mid in enumerate(shuffled):
        assert by_id[mid] == idx


def test_soft_delete_hides_from_customer_but_keeps_snapshot(db):
    store = make_store(db)
    cat = make_category(db, store.id)
    m = make_menu(db, store.id, cat.id, "김치찌개", 9000)
    table = make_table(db, store.id, number="1")
    sess = make_session(db, table)
    ctx = session_ctx(store.id, table, sess)

    # 주문 생성(스냅샷 저장)
    r = order_service.create_order(ctx, f"k-{uuid.uuid4()}", [OrderItemIn(menu_id=m.id, quantity=2)])
    assert r["items"][0]["menu_name"] == "김치찌개"

    # 소프트 삭제
    mgmt_service.soft_delete_menu(store.id, m.id)

    # 고객 조회에서 제외
    customer_view = menu_service.list_menu_by_category(db, store.id)
    all_menu_ids = [mm["id"] for c in customer_view for mm in c["menus"]]
    assert m.id not in all_menu_ids

    # 기존 주문 스냅샷은 유지
    orders = order_service.list_current_orders(db, ctx)
    assert orders[0]["items"][0]["menu_name"] == "김치찌개"
    assert orders[0]["items"][0]["unit_price"] == 9000
