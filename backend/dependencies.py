from typing import TypeVar

import g4f
from fastapi import Query
from fastapi.openapi.models import Example
from g4f import ModelUtils, ProviderModelMixin
from pydantic import BaseModel, Field

from backend.models import CompletionProvider, Message

all_models = list(ModelUtils.convert.keys())

all_working_providers: list[CompletionProvider] = [
    CompletionProvider(
        name=provider.__name__,
        supported_models=provider.models
        if isinstance(provider, ProviderModelMixin)
        else [],
    )
    for provider in g4f.Provider.__providers__
    if provider.working
]

A = TypeVar("A")


def generate_examples_from_values(values: list) -> dict[str, Example]:
    return {str(v or "--"): Example(value=v) for v in values}


def allowed_values_or_none(v: A | None, allowed: list[A]) -> A | None:
    if v is None:
        return v
    if v not in allowed:
        raise ValueError(f"Value {v} not in allowed values: {allowed}")
    return v


class CompletionParams:
    def __init__(
        self,
        model: str | None = Query(
            None,
            description="LLM model to use for completion. Cannot be specified together with provider.",
            openapi_examples=generate_examples_from_values([None] + all_models),
        ),
        provider: str | None = Query(
            None,
            description="Provider to use for completion. Cannot be specified together with model.",
            openapi_examples=generate_examples_from_values(
                [None] + all_working_providers
            ),
        ),
    ):
        provider = provider or None
        model = model or None
        if model and provider:
            raise ValueError("model and provider cannot be provided together yet")
        if not (model or provider):
            raise ValueError("one of model or provider must be specified")

        allowed_values_or_none(model, all_models)
        allowed_values_or_none(provider, all_working_providers)

        self.model = model
        self.provider = provider


def chat_completion() -> type[g4f.ChatCompletion]:
    return g4f.ChatCompletion


class CompletionResponse(BaseModel):
    completion: str = Field(..., description="Completion of the messages")


class UiCompletionRequest(BaseModel):
    message: str = Field(..., description="Current message from text input")
    model: str = Field(..., description="Model to use for completion")
    provider: str = Field(..., description="Provider to use for completion")
    history: list[Message] = Field(
        default_factory=list, description="History of past messages"
    )
