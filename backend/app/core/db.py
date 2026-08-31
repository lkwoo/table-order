"""U0 Core - DB 엔진/세션 + Unit-of-Work 트랜잭션 유틸.

트랜잭션 정책 (U0 business-rules §2):
- 쓰기 서비스가 트랜잭션 경계를 소유한다 (Repository는 트랜잭션 미개시).
- 이벤트 발행은 커밋 성공 후에만 수행한다.
"""
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI 의존성: 요청 스코프 DB 세션."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def unit_of_work() -> Iterator[Session]:
    """서비스 레이어용 명시적 트랜잭션 경계.

    with unit_of_work() as db:
        ... 다중 쓰기 ...
    # 정상 종료 시 commit, 예외 시 rollback (원자성)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
