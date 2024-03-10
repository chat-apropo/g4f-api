from typing import TypeVar

import g4f
from fastapi import Query
from fastapi.openapi.models import Example
from g4f import ModelUtils, ProviderModelMixin
from g4f.models import RetryProvider
from pydantic import BaseModel, Field

from backend.models import CompletionModel, CompletionProvider, Message

g4f_working_providers_map = {
    provider.__name__: provider
    for provider in g4f.Provider.__providers__
    if provider.working
}
all_working_provider_names: list[str] = list(g4f_working_providers_map.keys())
all_working_providers_map: dict[str, CompletionProvider] = {}

all_model_names = list(ModelUtils.convert.keys())
all_models_map: dict[str, CompletionModel] = {}

for model_name in all_model_names:
    model = ModelUtils.convert[model_name]
    best_providers = set([model.base_provider])

    # Retry providers contain multiple recomendations
    if isinstance(model.best_provider, RetryProvider):
        best_providers.update([p.__name__ for p in model.best_provider.providers])
    else:
        best_providers.add(model.best_provider.__name__)

    complation_model = CompletionModel(
        name=model.name, supported_provider_names=best_providers
    )
    all_models_map[model_name] = complation_model

    # Populate providers with recomended models
    for provider_name in best_providers:
        if provider_name not in all_working_providers_map:
            all_working_providers_map[provider_name] = CompletionProvider(
                name=provider_name,
                supported_models=set(),
                url=g4f_working_providers_map[provider_name].url
                if provider_name in g4f_working_providers_map
                else "",
            )
        all_working_providers_map[provider_name].supported_models.add(model.name)

# ProviderMixins also have models directly associated with them
for provider in g4f.Provider.__providers__:
    if not provider.working:
        continue
    if (
        isinstance(provider, ProviderModelMixin)
        and provider.__name__ in all_working_providers_map
    ):
        all_working_providers_map[provider.__name__].supported_models.update(
            provider.models
        )


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
            openapi_examples=generate_examples_from_values([None] + all_model_names),
        ),
        provider: str | None = Query(
            None,
            description="Provider to use for completion. Cannot be specified together with model.",
            openapi_examples=generate_examples_from_values(
                [None] + all_working_provider_names
            ),
        ),
    ):
        provider = provider or None
        model = model or None
        if model and provider:
            raise ValueError("model and provider cannot be provided together yet")
        if not (model or provider):
            raise ValueError("one of model or provider must be specified")

        allowed_values_or_none(model, all_model_names)
        allowed_values_or_none(provider, all_working_provider_names)

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
