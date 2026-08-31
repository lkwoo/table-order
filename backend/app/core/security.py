"""U0/U1 - 보안: bcrypt 해싱, JWT 발급/검증, AuthGuard 의존성.

business-rules: 비밀번호 bcrypt만 저장, 관리자 JWT 16h, 세션 토큰 16h.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Query, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import unauthorized
from app.core.models import SessionStatus, TableSession

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---- 비밀번호 ----
def hash_password(raw: str) -> str:
    return _pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd.verify(raw, hashed)


# ---- JWT (관리자) ----
def create_admin_token(admin_id: uuid.UUID, store_id: uuid.UUID) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_exp_hours)
    payload = {
        "admin_id": str(admin_id),
        "store_id": str(store_id),
        "exp": expires_at,
        "typ": "admin",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


@dataclass
class AdminContext:
    admin_id: uuid.UUID
    store_id: uuid.UUID


def _decode_admin(token: str) -> AdminContext:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("typ") != "admin":
            raise unauthorized()
        return AdminContext(
            admin_id=uuid.UUID(payload["admin_id"]),
            store_id=uuid.UUID(payload["store_id"]),
        )
    except (JWTError, KeyError, ValueError):
        raise unauthorized("세션이 만료되었거나 유효하지 않습니다.")


def _extract_bearer(request: Request, token_q: str | None) -> str:
    # SSE는 쿼리 token=, 일반 요청은 Authorization 헤더
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    if token_q:
        return token_q
    raise unauthorized("인증 토큰이 없습니다.")


def get_current_admin(
    request: Request,
    token: str | None = Query(default=None),
) -> AdminContext:
    """관리자 JWT 가드 (헤더 Bearer 또는 SSE 쿼리 token)."""
    return _decode_admin(_extract_bearer(request, token))


# ---- 테이블 세션 토큰 ----
@dataclass
class SessionContext:
    session_id: uuid.UUID
    table_id: uuid.UUID
    store_id: uuid.UUID
    expires_at: datetime


def _extract_session_token(request: Request, token_q: str | None) -> str:
    header = request.headers.get("X-Session-Token")
    if header:
        return header
    if token_q:
        return token_q
    raise unauthorized("세션 토큰이 없습니다.")


def get_current_session(
    request: Request,
    db: Session = Depends(get_db),
    token: str | None = Query(default=None),
) -> SessionContext:
    """테이블 세션 가드: token 유효 + status=active + 미만료 (business-rules R4/R6)."""
    raw = _extract_session_token(request, token)
    sess = db.execute(select(TableSession).where(TableSession.token == raw)).scalar_one_or_none()
    if sess is None or sess.status != SessionStatus.active:
        raise unauthorized("세션이 유효하지 않습니다.")
    # 만료 판단: now >= expires_at
    now = datetime.now(timezone.utc)
    expires = sess.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now >= expires:
        raise unauthorized("세션이 만료되었습니다. 다시 로그인해주세요.")
    # store_id 도출
    from app.core.models import Table  # 지역 임포트(순환 방지)

    table = db.get(Table, sess.table_id)
    if table is None:
        raise unauthorized()
    return SessionContext(
        session_id=sess.id,
        table_id=sess.table_id,
        store_id=table.store_id,
        expires_at=expires,
    )
