"""테스트 픽스처: SQLite in-memory (StaticPool 단일 연결)로 서비스 계층 검증.

app.core.db.SessionLocal을 테스트 엔진에 재바인딩하여
서비스가 생성하는 세션(unit_of_work)도 동일 DB를 사용하게 한다.
"""
import pytest
from hypothesis import HealthCheck, settings
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core import db as db_module
from app.core.models import Base

# 함수 스코프 db 픽스처는 예제마다 재설정되지 않지만, 각 예제가
# 고유 UUID(store/table/menu)를 생성하므로 예제 간 격리가 유지된다.
settings.register_profile(
    "pbt", suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
settings.load_profile("pbt")


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    db_module.engine = engine
    db_module.SessionLocal.configure(bind=engine)
    session = db_module.SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
