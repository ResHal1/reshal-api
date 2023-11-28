from enum import Enum
from functools import lru_cache

from pydantic import BaseSettings

from reshal_api import __version__


class Environment(str, Enum):
    LOCAL = "LOCAL"
    TESTING = "TESTING"
    PRODUCTION = "PRODUCTION"

    @property
    def is_local(self):
        return self == Environment.LOCAL

    @property
    def is_testing(self):
        return self == Environment.TESTING

    @property
    def is_debug(self):
        return self in {Environment.LOCAL, Environment.TESTING}

    @property
    def is_production(self):
        return self == Environment.PRODUCTION


class CORSSettings(BaseSettings):
    allow_origins: list[str] = ["*"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    allow_credentials: bool = True

    class Config:
        env_prefix = "CORS_"
        case_sensitive = False


class UvicornSettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8080
    workers: int = 1
    reload: bool = True

    class Config:
        env_prefix = "UVICORN_"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    USER: str = "reshal"
    PASSWORD: str = "reshal123"
    HOST: str = "127.0.0.1"
    PORT: int = 5432
    NAME: str = "reshaldb"
    DRIVER: str = "asyncpg"

    class Config:
        env_prefix = "DB_"

    @property
    def url(self) -> str:
        return f"postgresql+{self.DRIVER}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


class Config(BaseSettings):
    TITLE: str = "Reshal API"
    OTLP_APP_NAME: str = TITLE.replace(" ", "_").lower()
    VERSION: str = __version__
    ROOT_PATH: str = "/"
    ENVIRONMENT: Environment = Environment.LOCAL
    SECRET_KEY: str = "secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_COOKIE_NAME: str = "reshal_access_token"
    ACCESS_TOKEN_EXPIRE: int = 43800  # 30 days
    STATIC_DIR: str = "static"
    OTLP_GRPC_ENDPOINT: str = "http://tempo:4317"
    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    AWS_REGION: str = "eu-north-1"
    EMAIL_WHITELIST: list[str] = ["admin@bartoszmagiera.dev"]

    class Config:
        env_prefix = "APP_"


@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()  # pyright: ignore
