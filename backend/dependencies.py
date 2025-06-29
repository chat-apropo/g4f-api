from dataclasses import dataclass, field
from typing import TypeVar

import g4f
from fastapi import Query
from fastapi.openapi.models import Example
from g4f.models import ModelUtils
from g4f.Provider import BaseProvider, RetryProvider
from g4f.Provider.base_provider import ProviderModelMixin
from pydantic import BaseModel, Field

from backend.errors import CustomValidationError
from backend.models import CompletionModel, CompletionProvider, Message

MODEL_BLACKLIST = [
    "TextGenerations",
    "ImageGenerations",
]

BEST_MODELS_ORDERED = [
    "gpt-4o-mini-audio",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4",
]
PROVIDER_BLACKLIST = {
    "AItianhuSpace",
    "Ollama",
    "Local",
    "Aura",
    "AiChatOnline",
    "Allyfy",
    "AIUncensored",
    "AmigoChat",
    "ChatGpt",
    "ChatGptEs",
    "Mhystical",
    "Custom",
    "HuggingFace",
    "CablyAI",
    "Yqcloud",
    "Goabror",
    "FreeRouter",
    "FreeGpt",
    "MarkItDown",
}

provider_models_override = {
    "ChatGpt": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4",
        "gpt-4-turbo",
        "chatgpt-4o-latest",
    ],
    "ChatGptEs": ["gpt-4o", "gpt-4o-mini", "chatgpt-4o-latest"],
}


base_working_providers_map = {
    provider.__name__: provider
    for provider in g4f.Provider.__providers__
    if provider.working
    and not provider.needs_auth
    and provider.__name__ not in PROVIDER_BLACKLIST
}


@dataclass
class ProviderAndModels:
    all_working_provider_names: list[str] = field(default_factory=list)
    all_working_providers_map: dict[str, CompletionProvider] = field(
        default_factory=dict
    )
    all_model_names: list[str] = field(default_factory=list)
    all_models_map: dict[str, CompletionModel] = field(default_factory=dict)

    def update_model_providers(
        self, working_providers_map: dict[str, BaseProvider]
    ) -> None:
        self.all_working_provider_names = list(working_providers_map.keys())
        self.all_working_providers_map = {}
        self.all_model_names = list(ModelUtils.convert.keys())
        self.all_models_map = {}

        for model_name in self.all_model_names:
            model = ModelUtils.convert[model_name]
            best_providers = set([model.base_provider])

            # Retry providers contain multiple recomendations
            if isinstance(model.best_provider, RetryProvider):
                best_providers.update(
                    [p.__name__ for p in model.best_provider.providers]
                )
            elif model.best_provider:
                best_providers.add(model.best_provider.__name__)
            else:
                continue

            complation_model = CompletionModel(
                name=model.name, supported_provider_names=best_providers
            )
            self.all_models_map[model_name] = complation_model

            # Populate providers with recomended models
            for provider_name in best_providers:
                if provider_name not in working_providers_map:
                    continue

                if provider_name not in self.all_working_providers_map:
                    self.all_working_providers_map[provider_name] = CompletionProvider(
                        name=provider_name,
                        supported_models=set(),
                        url=working_providers_map[provider_name].url or "",
                    )
                self.all_working_providers_map[provider_name].supported_models.add(
                    model.name
                )

        # Populate with models declared in the provider class definitions themselves
        for provider_name in working_providers_map:
            if provider_name not in working_providers_map:
                continue
            provider: BaseProvider = working_providers_map[provider_name]
            if provider_name not in self.all_working_providers_map:
                self.all_working_providers_map[provider_name] = CompletionProvider(
                    name=provider_name,
                    supported_models=set(),
                    url=provider.url or "",
                )
            if hasattr(provider, "models"):
                for model in provider.models:
                    if isinstance(model, str):
                        self.all_working_providers_map[
                            provider_name
                        ].supported_models.add(model)
                    elif isinstance(model, dict):
                        self.all_working_providers_map[
                            provider_name
                        ].supported_models.update(set(model.keys()))

            if hasattr(provider, "default_model"):
                self.all_working_providers_map[provider_name].supported_models.update(
                    [provider.default_model] if provider.default_model else []
                )

            if hasattr(provider, "supports_gpt_4") and provider.supports_gpt_4:
                self.all_working_providers_map[provider_name].supported_models.add(
                    "gpt-4"
                )

            if (
                hasattr(provider, "supports_gpt_35_turbo")
                and provider.supports_gpt_35_turbo
            ):
                self.all_working_providers_map[provider_name].supported_models.add(
                    "gpt-3.5-turbo"
                )

            for model_name in self.all_working_providers_map[
                provider_name
            ].supported_models:
                if model_name not in self.all_models_map:
                    self.all_models_map[model_name] = CompletionModel(
                        name=model_name, supported_provider_names={provider_name}
                    )
                else:
                    self.all_models_map[model_name].supported_provider_names.add(
                        provider_name
                    )

        # ProviderMixins also have models directly associated with them
        for provider in g4f.Provider.__providers__:
            if not provider.working:
                continue
            provider_name = provider.__name__
            if (
                isinstance(provider, ProviderModelMixin)
                and provider_name in self.all_working_providers_map
            ):
                self.all_working_providers_map[provider_name].supported_models.update(
                    provider.models
                )
                for model_name in self.all_working_providers_map[
                    provider_name
                ].supported_models:
                    if model_name not in self.all_models_map:
                        self.all_models_map[model_name] = CompletionModel(
                            name=model_name, supported_provider_names={provider_name}
                        )
                    else:
                        self.all_models_map[model_name].supported_provider_names.add(
                            provider_name
                        )

        self.all_model_names = list(self.all_models_map.keys())

        for provider_name in provider_models_override:
            if provider_name in self.all_working_providers_map:
                self.all_working_providers_map[provider_name].supported_models = set(
                    provider_models_override[provider_name]
                )


provider_and_models = ProviderAndModels()
provider_and_models.update_model_providers(base_working_providers_map)

BEST_MODELS_ORDERED += [
    model_name
    for model_name in provider_and_models.all_model_names
    if model_name not in BEST_MODELS_ORDERED and model_name not in MODEL_BLACKLIST
]

A = TypeVar("A")


def generate_examples_from_values(values: list) -> dict[str, Example]:
    return {str(v or "--"): Example(value=v) for v in values}


def allowed_values_or_none(v: A | None, allowed: list[A]) -> A | None:
    if v is None:
        return v
    if v not in allowed:
        raise CustomValidationError(
            f"Value {v} not in allowed values: {allowed}", error={}
        )
    return v


class CompletionParams:
    def __init__(
        self,
        model: str | None = Query(
            None,
            description="LLM model to use for completion. If not specified, the best available model will be used.",
            openapi_examples=generate_examples_from_values(
                [None] + provider_and_models.all_model_names
            ),
        ),
        provider: str | None = Query(
            None,
            description="Provider to use for completion. If not specified, the best available provider will be used.",
            openapi_examples=generate_examples_from_values(
                [None] + provider_and_models.all_working_provider_names
            ),
        ),
    ):
        provider = provider or None
        model = model or None
        if not (model or provider):
            self.provider = None
            self.model = None
            return

        allowed_values_or_none(model, provider_and_models.all_model_names)
        allowed_values_or_none(provider, provider_and_models.all_working_provider_names)
        if model and provider:
            if provider not in provider_and_models.all_working_providers_map:
                raise CustomValidationError(
                    f"Provider {provider} not in working providers. Check available providers with /api/providers",
                    error={
                        "allowed_providers": provider_and_models.all_working_provider_names
                    },
                )
            provider_model = provider_and_models.all_working_providers_map[provider]
            if model not in provider_model.supported_models:
                raise CustomValidationError(
                    f"Model {model} not supported by provider {provider}. Check available providers and their supported models with /api/providers",
                    error={"allowed_models": list(provider_model.supported_models)},
                )

        self.provider = provider
        self.model = model


def chat_completion() -> type[g4f.ChatCompletion]:
    return g4f.ChatCompletion


class CompletionResponse(BaseModel):
    completion: str = Field(..., description="Completion of the messages")
    provider: str | None = Field(None, description="Provider used for completion")
    model: str | None = Field(None, description="Model used for completion")


class UiCompletionRequest(BaseModel):
    model: str | None = Field(
        None,
        description="Model to use for completion. If not specified, the best available model will be used.",
    )
    provider: str | None = Field(
        None,
        description="Provider to use for completion. If not specified, the best available provider will be used.",
    )
    message: str = Field(..., description="Current message from text input")
    history: list[Message] = Field(
        default_factory=list, description="History of past messages"
    )
