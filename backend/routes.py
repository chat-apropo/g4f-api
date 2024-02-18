import g4f
from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import RedirectResponse

from backend.dependencies import CompletionParams, CompletionRequest, all_models, all_working_providers, chat_completion

router_root = APIRouter()
router_api = APIRouter(prefix="/api")


def add_routers(app: FastAPI) -> None:
    app.include_router(router_root)
    app.include_router(router_api)


@router_root.get("/")
def get_root():
    return RedirectResponse(url="/docs")


@router_api.post("/completions")
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


@router_api.get("/providers")
def get_list_providers():
    return {"providers": all_working_providers}


@router_api.get("/models")
def get_list_models():
    return {"models": all_models}


@router_api.get("/health")
def get_health_check():
    return {"status": "ok"}
