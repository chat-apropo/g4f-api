from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.errors import add_exception_handlers
from backend.routes import add_routers
from backend.settings import TEMPLATES_PATH

app = FastAPI(
    title="G4F API",
    description="Get text completions from various models and providers using https://github.com/xtekky/gpt4free",
    version="0.0.1",
)

add_exception_handlers(app)
add_routers(app)
app.mount("/static", StaticFiles(directory=TEMPLATES_PATH), name="static")

__all__ = ["app"]
