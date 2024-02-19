import uvicorn

from backend.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=1,
        timeout_keep_alive=30,
    )
