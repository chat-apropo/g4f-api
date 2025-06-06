import logging
from functools import lru_cache
from typing import NamedTuple

import g4f
import requests
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.adapters import adapt_response
from backend.dependencies import (
    BEST_MODELS_ORDERED,
    CompletionParams,
    CompletionResponse,
    Message,
    UiCompletionRequest,
    chat_completion,
    provider_and_models,
)
from backend.errors import CustomValidationError
from backend.models import CompletionRequest
from backend.settings import TEMPLATES_PATH

router_root = APIRouter()
router_api = APIRouter(prefix="/api")
router_ui = APIRouter(prefix="/app")


def add_routers(app: FastAPI) -> None:
    app.include_router(router_root)
    app.include_router(router_api)
    app.include_router(router_ui)


@router_root.get("/")
def get_root():
    return RedirectResponse(url=router_ui.prefix)


class NofailParms(NamedTuple):
    model: str
    provider: str


def get_nofail_params(offset: int = 0) -> NofailParms:
    for model in BEST_MODELS_ORDERED:
        try:
            provider = g4f.get_model_and_provider(model, None, False)[1]
        except g4f.errors.ModelNotFoundError:
            logging.warning(f"Model not found: {model}")
            continue

        # If the provider is not working, try to find another one that supports the model
        if provider.__name__ not in provider_and_models.all_working_provider_names:
            if offset > 0:
                offset -= 1
                continue
            for provider_name in provider_and_models.all_working_provider_names:
                if (
                    model
                    in provider_and_models.all_working_providers_map[
                        provider_name
                    ].supported_models
                ):
                    return NofailParms(model=model, provider=provider_name)

    raise HTTPException(
        status_code=500, detail="Failed to find a model and provider to use"
    )


def get_best_model_for_provider(provider_name: str) -> str:
    provider = provider_and_models.all_working_providers_map.get(provider_name)
    if provider is None:
        raise HTTPException(
            status_code=422, detail=f"Provider not found: {provider_name}"
        )
    models = list(provider.supported_models)
    if not models:
        raise HTTPException(
            status_code=422,
            detail=f"No models supported by provider: {provider_name}. Please specify a model.",
        )

    def _sort_key(model: str) -> int:
        return BEST_MODELS_ORDERED.index(model) if model in BEST_MODELS_ORDERED else 999

    models.sort(key=_sort_key)
    return models[0]


@lru_cache(maxsize=1)
def get_public_ip() -> str | None:
    response = requests.get("https://api.ipify.org?format=json")
    if not response.ok:
        return None
    return response.json().get("ip")


@router_api.post("/completions")
def post_completion(
    completion: CompletionRequest,
    params: CompletionParams = Depends(),
    chat: type[g4f.ChatCompletion] = Depends(chat_completion),
) -> CompletionResponse:
    nofail = False
    if params.model is None:
        if params.provider is None:
            model_name, provider_name = get_nofail_params()
            nofail = True
        else:
            provider_name = params.provider
            model_name = get_best_model_for_provider(provider_name)
    else:
        model_name = params.model
        provider_name = params.provider

    ip_detected_response: CompletionResponse | None = None
    for attempt in range(10):
        print(f"Trying model: {model_name} and provider: {provider_name}")
        try:
            response = chat.create(
                model=model_name,
                provider=provider_name,
                messages=[msg.model_dump() for msg in completion.messages],
                stream=False,
            )
            if isinstance(response, str):
                if response.strip() == "" and nofail:
                    model_name, provider_name = get_nofail_params(attempt)
                    model_name = get_best_model_for_provider(provider_name)
                    continue

                completion_response = CompletionResponse(
                    completion=adapt_response(model_name, response),
                    model=model_name,
                    provider=provider_name,
                )

                # HACK: Workaround for IP ban from some providers
                ip = get_public_ip()
                if ip is not None and ip in response.lower():
                    if ip_detected_response is not None:
                        ip_detected_response = completion_response
                    continue

                return completion_response

            raise CustomValidationError(
                "Unexpected response type from g4f.ChatCompletion.create",
                error={"response": str(response)},
            )
        except Exception as e:
            if not nofail:
                raise e
            provider_name = get_nofail_params(attempt).provider
            model_name = get_best_model_for_provider(provider_name)

    # Better than nothing maybe
    if ip_detected_response is not None:
        return ip_detected_response

    raise HTTPException(
        status_code=500,
        detail=f"Failed to get a response from the provider. Last tried model: {model_name} and provider: {provider_name}",
    )


@router_api.get("/providers")
def get_list_providers():
    return provider_and_models.all_working_providers_map


@router_api.get("/models")
def get_list_models():
    return provider_and_models.all_models_map


@router_api.get("/health")
def get_health_check():
    return {"status": "ok"}


### UI routes

templates = Jinja2Templates(directory=TEMPLATES_PATH)


@router_ui.get("/")
def get_ui(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={
            "all_models": provider_and_models.all_model_names,
            "all_providers": [""] + provider_and_models.all_working_provider_names,
            "default_model": "gpt-4",
        },
    )


@router_ui.post("/completions")
def get_completions(
    request: Request,
    payload: UiCompletionRequest,
    chat: type[g4f.ChatCompletion] = Depends(chat_completion),
) -> HTMLResponse:
    user_request = Message(role="user", content=payload.message)
    completion = post_completion(
        CompletionRequest(messages=payload.history + [user_request]),
        CompletionParams(model=payload.model, provider=payload.provider),
        chat=chat,
    )
    bot_response = Message(role="assistant", content=completion.completion)
    return templates.TemplateResponse(
        name="messages.html",
        request=request,
        context={
            "messages": [user_request, bot_response],
        },
    )
