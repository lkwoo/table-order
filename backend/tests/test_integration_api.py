"""통합 테스트: HTTP 계층에서 유닛 간 상호작용 검증.

시드된 앱을 TestClient(SQLite in-memory)로 기동하여
관리자 로그인 → 테이블 생성 → 테이블 로그인 → 메뉴 조회 →
주문 생성 → 대시보드 집계 → 상태 전이(정상/거부) 전 흐름을 확인한다.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core import db as db_module
from app.core.models import Base

STORE_ID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    db_module.engine = engine
    db_module.SessionLocal.configure(bind=engine)
    from app.main import app  # 지연 임포트 (엔진 재바인딩 이후)

    with TestClient(app) as c:  # lifespan → create_all + seed_if_empty
        yield c
    Base.metadata.drop_all(engine)


def _admin_headers(client) -> dict:
    r = client.post(
        "/api/auth/admin-login",
        json={"store_id": STORE_ID, "username": "admin", "password": "admin1234"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_full_order_flow(client):
    admin = _admin_headers(client)

    # 테이블 생성
    r = client.post(
        "/api/admin/tables", headers=admin, json={"table_number": "5", "password": "1234"}
    )
    assert r.status_code == 201, r.text

    # 테이블 로그인
    r = client.post(
        "/api/auth/table-login",
        json={"store_id": STORE_ID, "table_number": "5", "password": "1234"},
    )
    assert r.status_code == 200, r.text
    session_token = r.json()["session_token"]
    sess_headers = {"X-Session-Token": session_token}

    # 메뉴 조회 (고객)
    r = client.get("/api/menus", headers=sess_headers)
    assert r.status_code == 200, r.text
    categories = r.json()
    menus = [m for c in categories for m in c["menus"]]
    assert len(menus) >= 2
    m1, m2 = menus[0], menus[1]
    expected_total = m1["price"] * 2 + m2["price"] * 1

    # 주문 생성 (서버 금액 재계산)
    r = client.post(
        "/api/orders",
        headers=sess_headers,
        json={
            "idempotency_key": str(uuid.uuid4()),
            "items": [
                {"menu_id": m1["id"], "quantity": 2},
                {"menu_id": m2["id"], "quantity": 1},
            ],
        },
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["total_amount"] == expected_total
    order_id = order["id"]

    # 대시보드 집계 확인 (관리자)
    r = client.get("/api/admin/dashboard", headers=admin)
    assert r.status_code == 200, r.text
    cards = r.json()
    card = next(c for c in cards if c["table_number"] == "5")
    assert card["total_amount"] == expected_total

    # 상태 전이: 대기중 → 준비중 (정상)
    r = client.patch(
        f"/api/admin/orders/{order_id}/status", headers=admin, json={"status": "준비중"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "준비중"

    # 상태 전이: 준비중 → 대기중 (역방향 거부, 409)
    r = client.patch(
        f"/api/admin/orders/{order_id}/status", headers=admin, json={"status": "대기중"}
    )
    assert r.status_code == 409, r.text


def test_admin_login_rejects_bad_password(client):
    r = client.post(
        "/api/auth/admin-login",
        json={"store_id": STORE_ID, "username": "admin", "password": "wrong"},
    )
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    r = client.get("/api/admin/dashboard")
    assert r.status_code in (401, 403)
