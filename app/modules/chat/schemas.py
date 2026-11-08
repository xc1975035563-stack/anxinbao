from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """发送消息或提交方案确认"""

    thread_id: UUID
    message: str | None = None
    decision: dict[str, Any] | None = None


class ChatMessageResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    additional_info: Any | None = None


class ChatHistoryResponse(BaseModel):
    thread_id: UUID
    messages: list[ChatMessageResponse]
    interrupt: None = None


class ProductBrief(BaseModel):
    name: str
    category: str
    insurer: str
    min_premium: str | None = None
    description: str = Field(default="")
