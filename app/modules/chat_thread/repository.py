from sqlalchemy.ext.asyncio import AsyncSession

from .models import ChatThread


class ChatThreadRepository:

    def __init__(self, session:AsyncSession):
        self.session = session

    """创建会话"""
    async def add(self, chat_thread: ChatThread):
        self.session.add(chat_thread)