"""U1 Auth - 로그인/세션 워크플로우 (business-logic-model 워크플로우 1~4)."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import unauthorized
from app.core.models import Admin, SessionStatus, Table, TableSession
from app.core.security import create_admin_token, verify_password


def admin_login(db: Session, store_id: uuid.UUID, username: str, password: str):
    """워크플로우 1: 관리자 로그인. 자격 오류는 존재 여부 미노출(R3)."""
    admin = db.execute(
        select(Admin).where(Admin.store_id == store_id, Admin.username == username)
    ).scalar_one_or_none()
    if admin is None or not verify_password(password, admin.password_hash):
        raise unauthorized("매장 ID, 사용자명 또는 비밀번호가 올바르지 않습니다.")
    token, expires_at = create_admin_token(admin.id, admin.store_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "store_id": admin.store_id,
        "admin_id": admin.id,
    }


def _get_or_create_active_session(db: Session, table: Table) -> TableSession:
    """table당 active 세션 최대 1개 (R5). 있으면 재사용, 없으면 생성."""
    existing = db.execute(
        select(TableSession).where(
            TableSession.table_id == table.id,
            TableSession.status == SessionStatus.active,
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if existing is not None:
        exp = existing.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now < exp:
            return existing
        # 만료된 active 세션 → ended 처리 후 신규 생성
        existing.status = SessionStatus.ended
        existing.ended_at = now
    sess = TableSession(
        table_id=table.id,
        token=secrets.token_urlsafe(32),
        status=SessionStatus.active,
        expires_at=now + timedelta(hours=settings.session_exp_hours),
    )
    db.add(sess)
    db.flush()
    return sess


def table_login(db: Session, store_id: uuid.UUID, table_number: str, password: str):
    """워크플로우 3: 테이블 초기 로그인."""
    table = db.execute(
        select(Table).where(Table.store_id == store_id, Table.table_number == table_number)
    ).scalar_one_or_none()
    if table is None or not verify_password(password, table.password_hash):
        raise unauthorized("테이블 번호 또는 비밀번호가 올바르지 않습니다.")
    sess = _get_or_create_active_session(db, table)
    db.commit()
    return {
        "session_token": sess.token,
        "table_id": table.id,
        "session_id": sess.id,
        "expires_at": sess.expires_at,
    }
