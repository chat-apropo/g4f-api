from functools import partial
from typing import Annotated, Literal, TypeVar

import g4f
from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from g4f.models import ModelUtils
from pydantic import AfterValidator, BaseModel, Field, root_validator

all_models = list(ModelUtils.convert.keys())

all_working_providers = [provider.__name__ for provider in g4f.Provider.__providers__ if provider.working]

A = TypeVar("A", bound=str)


def allowed_values(v: A, allowed: list[A]) -> A:
    if v not in allowed:
        raise ValueError(f"Value {v} not in allowed values: {allowed}")
    return v


class Message(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Who is sending the message")
    content: str = Field(..., description="Content of the message")


class CompletionRequest(BaseModel):
    model: Annotated[str | None, AfterValidator(partial(allowed_values, allowed=all_models))] = Field(
        None,
        description="LLM model to use for completion. Cannot be specified together with provider.",
        examples=all_models,
    )
    provider: Annotated[str | None, AfterValidator(partial(allowed_values, allowed=all_working_providers))] = Field(
        None,
        description="Provider to use for completion. Cannot be specified together with model.",
        examples=all_working_providers,
    )
    messages: list[Message] = Field(..., description="List of messages to use for completion")

    @root_validator(pre=True)
    def model_xor_provider(cls, values):
        if "model" in values and "provider" in values:
            raise ValueError("model and provider cannot be specified together")
        if "model" not in values and "provider" not in values:
            raise ValueError("model or provider must be specified")
        return values


def chat_completion() -> type[g4f.ChatCompletion]:
    return g4f.ChatCompletion


app = FastAPI()


@app.get("/")
def get_root():
    return RedirectResponse(url="/docs")


@app.post("/")
def post_completion(completion: CompletionRequest, chat: type[g4f.ChatCompletion] = Depends(chat_completion)):
    response = chat.create(
        model=completion.model,
        provider=completion.provider,
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
