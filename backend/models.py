from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    role: Literal["user", "assistant"] = Field(
        ..., description="Who is sending the message"
    )
    content: str = Field(..., description="Content of the message")


class CompletionRequest(BaseModel):
    messages: list[Message] = Field(
        ..., description="List of messages to use for completion"
    )
    model_config = ConfigDict(extra="forbid")


class CompletionProvider(BaseModel):
    name: str
    supported_models: list[str]
