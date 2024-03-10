from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


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


class CompletionModel(BaseModel):
    name: str
    supported_provider_names: set[str]

    @field_serializer("supported_provider_names")
    @classmethod
    def serialize_supported_provider_names(cls, v: set[str]) -> list[str]:
        return list(v)


class CompletionProvider(BaseModel):
    name: str
    url: str
    supported_models: set[str]

    @field_serializer("supported_models")
    @classmethod
    def serialize_supported_models(cls, v: set[str]) -> list[str]:
        return list(v)
