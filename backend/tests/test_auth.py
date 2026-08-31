"""U1 Auth - 비밀번호 해시 라운드트립 + 로그인 규칙 (PBT).

- bcrypt 해시는 원문과 다르며 verify는 항상 참, 오답은 거짓
- 관리자 로그인 실패는 존재 여부 미노출 (R3): 항상 401
- 테이블 로그인 → active 세션 최대 1개 (R5), 재로그인 시 동일 세션 재사용
"""
from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from app.auth import service as auth_service
from app.core.models import Admin, SessionStatus, TableSession
from app.core.security import hash_password, verify_password
from tests.factories import make_store, make_table

# bcrypt는 72바이트 초과 입력을 거부하므로 애플리케이션 제약(4~30자 ASCII)에 맞춘다.
_passwords = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=4, max_size=30
)


@settings(max_examples=30, deadline=None)
@given(pw=_passwords)
def test_password_hash_roundtrip(pw):
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h) is True
    assert verify_password(pw + "x", h) is False


def test_admin_login_success(db):
    store = make_store(db)
    admin = Admin(store_id=store.id, username="admin", password_hash=hash_password("admin1234"))
    db.add(admin)
    db.commit()

    result = auth_service.admin_login(db, store.id, "admin", "admin1234")
    assert result["token_type"] == "bearer"
    assert result["store_id"] == store.id


@settings(max_examples=20, deadline=None)
@given(username=st.text(min_size=1, max_size=12), password=st.text(min_size=1, max_size=12))
def test_admin_login_non_enumeration(db, username, password):
    # 존재하지 않는 계정/오답 모두 동일하게 401 (R3)
    store = make_store(db)
    with pytest.raises(HTTPException) as exc:
        auth_service.admin_login(db, store.id, username, password + "-wrong")
    assert exc.value.status_code == 401


def test_table_login_reuses_active_session(db):
    store = make_store(db)
    table = make_table(db, store.id, number="7", password="1234")

    r1 = auth_service.table_login(db, store.id, "7", "1234")
    r2 = auth_service.table_login(db, store.id, "7", "1234")
    assert r1["session_id"] == r2["session_id"]  # R5: 동일 active 세션 재사용

    active = db.execute(
        select(TableSession).where(
            TableSession.table_id == table.id, TableSession.status == SessionStatus.active
        )
    ).scalars().all()
    assert len(active) == 1


def test_table_login_wrong_password(db):
    store = make_store(db)
    make_table(db, store.id, number="7", password="1234")
    with pytest.raises(HTTPException) as exc:
        auth_service.table_login(db, store.id, "7", "0000")
    assert exc.value.status_code == 401
