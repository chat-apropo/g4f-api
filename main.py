from typing import Literal

import g4f
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"] = Field(description="assert if the message is by the user or the AI", examples=["user", "assistant"])
    content: str = Field(description="message contents")


class Completion(BaseModel):
    model: str = Field(description="LLMM to use", examples=["gpt-4", "gpt-3.5-turbo"]) 
    messages: list[Message] = Field(description="List of messages to send")  


app = FastAPI()


@app.post("/")
def test(completion: Completion):
    response = g4f.ChatCompletion.create(
        model=completion.model, messages=[msg.model_dump() for msg in completion.messages], stream=False
        )
    return {"message": response}
