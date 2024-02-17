import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    def _(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    def _(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content=json.loads(exc.json()))
