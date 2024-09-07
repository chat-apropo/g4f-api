from typing import TypeVar

import g4f
from fastapi import Query
from fastapi.openapi.models import Example
from g4f.models import ModelUtils
from g4f.Provider import BaseProvider, RetryProvider
from g4f.Provider.base_provider import ProviderModelMixin
from pydantic import BaseModel, Field

from backend.models import CompletionModel, CompletionProvider, Message

working_providers_map = {
    provider.__name__: provider
    for provider in g4f.Provider.__providers__
    if provider.working and not provider.needs_auth
}

all_working_provider_names: list[str] = list(working_providers_map.keys())
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
        if provider_name not in working_providers_map:
            continue

        if provider_name not in all_working_providers_map:
            all_working_providers_map[provider_name] = CompletionProvider(
                name=provider_name,
                supported_models=set(),
                url=working_providers_map[provider_name].url or "",
            )
        all_working_providers_map[provider_name].supported_models.add(model.name)

# Populate with models declared in the provider class definitions themselves
for provider_name in working_providers_map:
    if provider_name not in working_providers_map:
        continue
    provider: BaseProvider = working_providers_map[provider_name]
    if provider_name not in all_working_providers_map:
        all_working_providers_map[provider_name] = CompletionProvider(
            name=provider_name,
            supported_models=set(),
            url=provider.url or "",
        )
    if hasattr(provider, "models"):
        all_working_providers_map[provider_name].supported_models.update(
            set(provider.models or [])
        )

    if hasattr(provider, "default_model"):
        all_working_providers_map[provider_name].supported_models.update(
            [provider.default_model] if provider.default_model else []
        )

    if hasattr(provider, "supports_gpt_4") and provider.supports_gpt_4:
        all_working_providers_map[provider_name].supported_models.add("gpt-4")

    if hasattr(provider, "supports_gpt_35_turbo") and provider.supports_gpt_35_turbo:
        all_working_providers_map[provider_name].supported_models.add("gpt-3.5-turbo")

    for model_name in all_working_providers_map[provider_name].supported_models:
        if model_name not in all_models_map:
            all_models_map[model_name] = CompletionModel(
                name=model_name, supported_provider_names={provider_name}
            )
        else:
            all_models_map[model_name].supported_provider_names.add(provider_name)


# ProviderMixins also have models directly associated with them
for provider in g4f.Provider.__providers__:
    if not provider.working:
        continue
    provider_name = provider.__name__
    if (
        isinstance(provider, ProviderModelMixin)
        and provider_name in all_working_providers_map
    ):
        all_working_providers_map[provider_name].supported_models.update(
            provider.models
        )
        for model_name in all_working_providers_map[provider_name].supported_models:
            if model_name not in all_models_map:
                all_models_map[model_name] = CompletionModel(
                    name=model_name, supported_provider_names={provider_name}
                )
            else:
                all_models_map[model_name].supported_provider_names.add(provider_name)

all_model_names = list(all_models_map.keys())

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
        if not (model or provider):
            raise ValueError("one of model or provider must be specified at least")

        allowed_values_or_none(model, all_model_names)
        allowed_values_or_none(provider, all_working_provider_names)
        if model and provider:
            if provider not in all_working_providers_map:
                raise ValueError(
                    f"Provider {provider} not in working providers. Check available providers with /api/providers"
                )
            provider_model = all_working_providers_map[provider]
            if model not in provider_model.supported_models:
                raise ValueError(
                    f"Model {model} not supported by provider {provider}. Check available providers and their supported models with /api/providers"
                )

        self.provider = provider
        self.model = model


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
