import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every

from backend.background import update_working_providers
from backend.errors import add_exception_handlers
from backend.routes import add_routers
from backend.settings import TEMPLATES_PATH, settings

app = FastAPI(
    title="G4F API",
    description="Get text completions from various models and providers using https://github.com/xtekky/gpt4free",
    version="0.0.1",
)

add_exception_handlers(app)
add_routers(app)
app.mount("/static", StaticFiles(directory=TEMPLATES_PATH), name="static")

logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


@app.on_event("startup")
@repeat_every(seconds=60 * 60, wait_first=2, on_exception=logging.exception)
async def selftest_providers() -> None:
    if settings.CHECK_WORKING_PROVIDERS:
        await update_working_providers()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
__all__ = ["app"]
