"""환경변수 검증. 비밀값은 로그나 응답에 출력하지 않습니다."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "production"] = "development"
    app_name: str = "소담상점"
    app_base_url: AnyHttpUrl = "http://127.0.0.1:8000"
    allowed_hosts: list[str] = ["127.0.0.1", "localhost"]
    database_url: SecretStr | None = None
    db_host: str | None = Field(default=None, validation_alias=AliasChoices("DB_HOST", "host"), repr=False)
    db_port: int = Field(default=5432, ge=1, le=65535, validation_alias=AliasChoices("DB_PORT", "port"))
    db_name: str | None = Field(default=None, validation_alias=AliasChoices("DB_NAME", "dbname"), repr=False)
    db_user: str | None = Field(default=None, validation_alias=AliasChoices("DB_USER", "user"), repr=False)
    db_password: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("DB_PASSWORD", "password"), repr=False
    )
    session_secret: SecretStr | None = None
    cookie_secure: bool = True

    @field_validator("database_url", "session_secret", "db_password", mode="before")
    @classmethod
    def normalize_empty_secret(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value):
        if value is None:
            return value
        try:
            url = make_url(value.get_secret_value())
            valid = (
                url.drivername in ("postgres", "postgresql", "postgresql+psycopg")
                and bool(url.host and url.database and url.username and url.password)
                and url.query.get("sslmode", "require")
                in ("require", "verify-ca", "verify-full")
            )
        except Exception:
            valid = False
        if not valid:
            raise ValueError("DATABASE_URL은 TLS를 사용하는 PostgreSQL 연결 URL이어야 합니다.")
        return value

    @field_validator("allowed_hosts")
    @classmethod
    def validate_hosts(cls, value):
        if not value or any(not host or "*" in host or "/" in host or "://" in host for host in value):
            raise ValueError("ALLOWED_HOSTS에 와일드카드 없는 호스트 이름을 지정하세요.")
        return value

    @model_validator(mode="after")
    def validate_environment(self):
        # URL을 우선하며, 분리된 설정은 비밀번호를 안전하게 인코딩해 메모리에서 조합합니다.
        if self.database_url is None and (
            any((self.db_host, self.db_name, self.db_user, self.db_password))
            or "db_port" in self.model_fields_set
        ):
            if not all((self.db_host, self.db_name, self.db_user, self.db_password)):
                raise ValueError("분리된 DB 설정에는 host, dbname, user, password가 모두 필요합니다.")
            url = URL.create(
                "postgresql+psycopg",
                username=self.db_user,
                password=self.db_password.get_secret_value(),
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                query={"sslmode": "require"},
            )
            self.database_url = self.validate_database_url(SecretStr(url.render_as_string(hide_password=False)))
        origin = AnyHttpUrl(self.app_base_url)
        if origin.username or origin.password or origin.query or origin.fragment or origin.path not in (None, "/"):
            raise ValueError("APP_BASE_URL에는 경로·쿼리·인증정보 없는 사이트 주소를 지정하세요.")
        if self.session_secret is None or len(self.session_secret.get_secret_value()) < 32:
            raise ValueError("SESSION_SECRET에 32자 이상의 임의 비밀값을 설정하세요.")
        if not self.cookie_secure and (
            self.app_env != "development"
            or origin.scheme != "http"
            or origin.host not in ("localhost", "127.0.0.1", "[::1]", "::1")
        ):
            raise ValueError("Secure 쿠키 해제는 개발 환경의 로컬 HTTP에서만 허용됩니다.")
        if self.app_env == "production":
            if origin.scheme != "https" or not self.cookie_secure:
                raise ValueError("운영 환경은 HTTPS와 COOKIE_SECURE=true가 필수입니다.")
            if self.database_url is None:
                raise ValueError("운영 환경에는 DATABASE_URL이 필요합니다.")
            if self.session_secret is None or len(self.session_secret.get_secret_value()) < 32:
                raise ValueError("운영 환경의 SESSION_SECRET은 32자 이상이어야 합니다.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
