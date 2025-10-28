from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

import yaml  # type: ignore
from loguru import logger
from pydantic import BaseModel, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Secrets(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )

    app_env: Literal["prod", "dev"] = "dev"

    postgres_db: SecretStr
    postgres_user: SecretStr
    postgres_password: SecretStr
    postgres_port: SecretStr

    def is_dev(self) -> bool:
        return self.app_env == "dev"

    @computed_field
    def sqlalchemy_url(self) -> str:
        host = "localhost" if self.is_dev() else "postgres"
        return f"postgresql+asyncpg://{self.postgres_user.get_secret_value()}:{self.postgres_password.get_secret_value()}@{host}:{int(self.postgres_port.get_secret_value())}/{self.postgres_db.get_secret_value()}"


class UvicornConfig(BaseModel):
    host: str
    port: int
    workers: int
    reload: bool


class Config(BaseModel):
    cors_allow_origins: list[str]

    uvicorn: UvicornConfig


def load_config(env: str) -> Config:
    with open(f"./config.{env}.yaml") as f:
        raw = yaml.safe_load(f)

    return Config(**raw)


secrets = Secrets()
config = load_config(secrets.app_env)
timezone = ZoneInfo("Europe/Moscow")


logger.info(f"Application environment: {secrets.app_env}")
