from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    CHECK_WORKING_PROVIDERS: bool = True
    DEBUG: bool = False
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
TEMPLATES_PATH = "static"

__all__ = ["settings"]
