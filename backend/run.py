import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
        timeout_keep_alive=30,
    )
