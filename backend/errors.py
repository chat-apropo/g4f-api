import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class CustomValidationError(ValueError):
    def __init__(self, message: str, error: dict[str, str | list[str]]) -> None:
        super().__init__(message)
        self.error = error


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CustomValidationError)
    def _(_: Request, exc: CustomValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422, content={"detail": str(exc), "error": exc.error}
        )

    @app.exception_handler(ValidationError)
    def _(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content=json.loads(exc.json()))
