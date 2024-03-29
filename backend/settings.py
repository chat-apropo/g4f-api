from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False


settings = Settings()
TEMPLATES_PATH = "static"

__all__ = ["settings"]
