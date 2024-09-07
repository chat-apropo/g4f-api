import g4f
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.dependencies import (
    CompletionParams,
    CompletionResponse,
    Message,
    UiCompletionRequest,
    UiShortCompletionRequest,
    chat_completion,
    provider_and_models,
)
from backend.models import CompletionRequest
from backend.settings import TEMPLATES_PATH

router_root = APIRouter()
router_api = APIRouter(prefix="/api")
router_ui = APIRouter(prefix="/app")


def add_routers(app: FastAPI) -> None:
    app.include_router(router_root)
    app.include_router(router_api)
    app.include_router(router_ui)


BEST_MODELS_ORDERED = [
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-3.5",
]
BEST_MODELS_ORDERED += [
    model_name
    for model_name in provider_and_models.all_model_names
    if model_name not in BEST_MODELS_ORDERED
]


@router_root.get("/")
def get_root():
    return RedirectResponse(url=router_ui.prefix)


def get_nofail_params():
    for i in range(10):
        model = BEST_MODELS_ORDERED[i]
        provider = g4f.get_model_and_provider(model, None, False)[1]

        # If the provider is not working, try to find another one that supports the model
        if provider.__name__ not in provider_and_models.all_working_provider_names:
            for provider_name in provider_and_models.all_working_provider_names:
                if (
                    model
                    in provider_and_models.all_working_providers_map[
                        provider_name
                    ].supported_models
                ):
                    completion_provider = provider_and_models.all_working_providers_map[
                        provider_name
                    ]
                    return CompletionParams(
                        model=model, provider=completion_provider.name
                    )
            else:
                # Try the next model
                continue

    raise HTTPException(
        status_code=500, detail="Failed to get a response from the provider"
    )


@router_api.post("/completions")
def post_completion(
    completion: CompletionRequest,
    params: CompletionParams = Depends(),
    chat: type[g4f.ChatCompletion] = Depends(chat_completion),
) -> CompletionResponse:
    response = chat.create(
        model=params.model,
        provider=params.provider,
        messages=[msg.model_dump() for msg in completion.messages],
        stream=False,
    )
    if isinstance(response, str):
        return CompletionResponse(
            completion=response, model=params.model, provider=params.provider
        )
    raise ValueError("Unexpected response type from g4f.ChatCompletion.create")


@router_api.post("/completions/nofail")
def post_completion_nofail(
    completion: CompletionRequest,
    chat: type[g4f.ChatCompletion] = Depends(chat_completion),
) -> CompletionResponse:
    params = get_nofail_params()
    response = chat.create(
        model=params.model,
        provider=params.provider,
        messages=[msg.model_dump() for msg in completion.messages],
        stream=False,
    )
    if isinstance(response, str):
        return CompletionResponse(
            completion=response, model=params.model, provider=params.provider
        )
    raise ValueError("Unexpected response type from g4f.ChatCompletion.create")


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


@router_ui.post("/completions/nofail")
def get_completions_nofail(
    request: Request,
    payload: UiShortCompletionRequest,
    chat: type[g4f.ChatCompletion] = Depends(chat_completion),
) -> HTMLResponse:
    params = get_nofail_params()
    user_request = Message(role="user", content=payload.message)
    completion = post_completion(
        CompletionRequest(messages=payload.history + [user_request]),
        CompletionParams(model=params.model, provider=params.provider),
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
