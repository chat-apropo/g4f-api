from typing import Literal

import g4f
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Completion(BaseModel):
    model: str
    messages: list[Message]


app = FastAPI()


@app.post("/")
def test(completion: Completion):
    response = g4f.ChatCompletion.create(
        model=completion.model, messages=[msg.model_dump() for msg in completion.messages], stream=False
        )
    return {"message": response}
