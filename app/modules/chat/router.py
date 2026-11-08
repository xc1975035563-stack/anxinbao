import json
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infra.database import get_session
from app.modules.chat.llm import FALLBACK_REPLY, ensure_model_configured, stream_reply
from app.modules.chat.schemas import ChatHistoryResponse, ChatRequest
from app.modules.chat.service import ChatService

logger = get_logger(__name__)

history_router = APIRouter(prefix="/api/v1/chat-threads", tags=["会话消息"])
chat_router = APIRouter(prefix="/api/v1", tags=["对话"])


def get_chat_service(session: AsyncSession = Depends(get_session)) -> ChatService:
    return ChatService(session)


@history_router.get("/{thread_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(
    thread_id: UUID,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: ChatService = Depends(get_chat_service),
) -> ChatHistoryResponse:
    """查询会话历史，没有待确认方案时 interrupt 为 null"""
    return await service.history(thread_id, user_id)


@chat_router.post("/chat")
async def chat(
    request: ChatRequest,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """流式回复。事件类型为 message。"""
    ensure_model_configured()
    history, catalog = await service.begin_turn(
        request.thread_id,
        user_id,
        request.message,
        request.decision,
    )

    async def events() -> AsyncIterator[str]:
        parts: list[str] = []
        try:
            async for text in stream_reply(history, catalog):
                parts.append(text)
                yield _sse("message", text)
        except Exception:
            logger.exception("对话模型生成失败, thread_id=%s", request.thread_id)
        reply = "".join(parts).strip()
        if not reply:
            reply = FALLBACK_REPLY
            yield _sse("message", reply)
        await service.save_assistant(request.thread_id, user_id, reply)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(event: str, data: object) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
