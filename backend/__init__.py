from fastapi import FastAPI

from backend.errors import add_exception_handlers
from backend.routes import router

app = FastAPI()

add_exception_handlers(app)
app.include_router(router)

__all__ = ["app"]
