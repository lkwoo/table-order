"""U0 Core - 애플리케이션 설정 (Pydantic Settings)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://app:app@db:5432/tableorder"

    # Auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_exp_hours: int = 16  # 관리자 세션 = 16시간 (requirements §3.2.1)
    session_exp_hours: int = 16  # 테이블 세션 = 16시간

    # CORS (개발 환경)
    cors_origins: str = "http://localhost:5173"

    # Domain rules
    price_min: int = 1_000
    price_max: int = 100_000
    quantity_min: int = 1
    quantity_max: int = 99
    history_retention_days: int = 90  # 3개월

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
