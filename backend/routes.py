import g4f
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.dependencies import (
    CompletionParams,
    CompletionRequest,
    CompletionResponse,
    Message,
    UiCompletionRequest,
    all_models,
    all_working_providers,
    chat_completion,
)
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
        return CompletionResponse(completion=response)
    raise ValueError("Unexpected response type from g4f.ChatCompletion.create")


@router_api.get("/providers")
def get_list_providers():
    return {"providers": all_working_providers}


@router_api.get("/models")
def get_list_models():
    return {"models": all_models}


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
            "all_models": all_models,
            "all_providers": [""] + all_working_providers,
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
