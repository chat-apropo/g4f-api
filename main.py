import g4f
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Completion(BaseModel):
    model: str
    messages: List[dict]

app = FastAPI(root_path="ai_api")

@app.post("/")
def test(completion: Completion):
    try:
        response = g4f.ChatCompletion.create(
            model=completion.model,
            messages=completion.messages,
            stream=False)
    except
        raise HTTPException(status_code=404, detail="error")
    return {"message": response }

