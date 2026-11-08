from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ChatMessage


class ChatMessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, message: ChatMessage) -> None:
        self.session.add(message)

    async def list_by_thread(self, thread_id: UUID) -> list[ChatMessage]:
        result = await self.session.scalars(
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        )
        return list(result.all())

    async def delete_by_thread(self, thread_id: UUID) -> None:
        await self.session.execute(
            delete(ChatMessage).where(ChatMessage.thread_id == thread_id)
        )
