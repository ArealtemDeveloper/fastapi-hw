from typing import Annotated
from urllib.parse import urlparse

from fastapi import Depends, Request
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, field_validator


class AppSettings(BaseModel):
    name: str
    debug: bool


class DatabaseSettigs(BaseModel):
    url: str


class AuthSettings(BaseModel):
    secret: str


class PostSettings(BaseModel):
    debounce_time: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Post Project"
    debug: bool = False

    database_url: str
    secret: str
    minimal_post_debounce_time: int

    @property
    def app(self) -> AppSettings:
        return AppSettings(name=self.app_name, debug=self.debug)

    @property
    def db(self) -> DatabaseSettigs:
        return DatabaseSettigs(url=self.database_url)

    @property
    def auth(self) -> AuthSettings:
        return AuthSettings(secret=self.secret)

    @property
    def post_settings(self) -> PostSettings:
        return PostSettings(debounce_time=self.minimal_post_debounce_time)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        parsed_value = urlparse(value)

        if parsed_value.scheme not in {"postgresql", "postgresql+asyncpg"}:
            raise ValueError(
                "database_url scheme must be postgresql or postgresql+asyncpg"
            )

        if not parsed_value.hostname:
            raise ValueError("database_url must include hostname")

        dbname = (parsed_value.path or "").lstrip("/")

        if not dbname:
            raise ValueError("database_url must include database")

        if parsed_value.port is not None and not (1 <= parsed_value.port <= 65535):
            raise ValueError("database_url port must be 1...65535")

        return value


def get_settings(request: Request):
    return request.app.state.settings


SettingsDeps = Annotated[Settings, Depends(get_settings)]
