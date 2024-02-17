import g4f
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from backend.dependencies import CompletionParams, CompletionRequest, all_models, all_working_providers, chat_completion

router = APIRouter()


@router.get("/")
def get_root():
    return RedirectResponse(url="/docs")


@router.post("/")
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


@router.get("/providers")
def get_list_providers():
    return {"providers": all_working_providers}


@router.get("/models")
def get_list_models():
    return {"models": all_models}


@router.get("/health")
def get_health_check():
    return {"status": "ok"}
