import json
from functools import partial
from typing import Annotated, Any, Literal, TypeVar

import g4f
from fastapi import Depends, FastAPI, Query, Request
from fastapi.openapi.models import Example
from fastapi.responses import JSONResponse, RedirectResponse
from g4f.models import ModelUtils
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError, model_validator

all_models = list(ModelUtils.convert.keys())

all_working_providers = [provider.__name__ for provider in g4f.Provider.__providers__ if provider.working]

A = TypeVar("A")


def create_example_dict(values: list) -> dict[str, Example]:
    return {str(v): Example(value=v) for v in values}


def allowed_values_or_none(v: A, allowed: list[A]) -> A:
    if v is None:
        return v
    if v not in allowed:
        raise ValueError(f"Value {v} not in allowed values: {allowed}")
    return v


class Message(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Who is sending the message")
    content: str = Field(..., description="Content of the message")


class CompletionRequest(BaseModel):
    messages: list[Message] = Field(..., description="List of messages to use for completion")
    model_config = ConfigDict(extra="forbid")


class CompletionParams(BaseModel):
    model: Annotated[str | None, AfterValidator(partial(allowed_values_or_none, allowed=all_models))] = Query(
        None,
        description="LLM model to use for completion. Cannot be specified together with provider.",
        openapi_examples=create_example_dict(all_models),
    )
    provider: Annotated[
        Annotated[str, None] | None,
        AfterValidator(partial(allowed_values_or_none, allowed=all_working_providers)),
    ] = Query(
        None,
        description="Provider to use for completion. Cannot be specified together with model.",
        openapi_examples=create_example_dict(all_working_providers),
    )
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    def model_xor_provider(cls, values: dict[str, Any]):
        if values.get("model") and values.get("provider"):
            raise ValueError("model and provider cannot be provided together yet")
        if not (values.get("model") or values.get("provider")):
            raise ValueError("one of model or provider must be specified")
        return values


def chat_completion() -> type[g4f.ChatCompletion]:
    return g4f.ChatCompletion


app = FastAPI()


@app.exception_handler(ValueError)
def throw_value_error(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
def throw_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content=json.loads(exc.json()))


@app.get("/")
def get_root():
    return RedirectResponse(url="/docs")


@app.post("/")
def post_completion(
    completion: CompletionRequest,
    params: CompletionParams = Depends(),
    chat: type[g4f.ChatCompletion] = Depends(chat_completion),
):
    response = chat.create(
        model=params.model,
        provider=params.provider,
        messages=[msg.model_dump() for msg in completion.messages],
        stream=False,
    )
    return {"completion": response}


@app.get("/providers")
def get_list_providers():
    return {"providers": all_working_providers}


@app.get("/models")
def get_list_models():
    return {"models": all_models}


@app.get("/health")
def get_health_check():
    return {"status": "ok"}
