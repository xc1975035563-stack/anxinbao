from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from .models import ChatThread


class ChatThreadRepository:

    '''查询方法'''
    async def list_by_user(self, user_id: int) -> list[ChatThread]:
        result = await self.session.scalars(
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(
                ChatThread.updated_at.desc(),
                ChatThread.created_at.desc(),
            )
        )
        return list(result.all())

    def __init__(self, session:AsyncSession):
        self.session = session

    """创建会话"""
    async def add(self, chat_thread: ChatThread):
        self.session.add(chat_thread)