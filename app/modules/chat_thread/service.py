from sqlalchemy.ext.asyncio import AsyncSession

from .repository import ChatThreadRepository
from .models import ChatThread

class ChatThreadService:

    async def list_by_user(self, user_id: int) -> list[ChatThread]:
        return await self.repository.list_by_user(user_id)

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ChatThreadRepository(session)

    async def add(self, user_id: int , title: str):
        # 用上下文管理，开启事务，运行完成，自动commit，出现异常，自动rollback
        async with self.session.begin():
            # 创建对象，对象 映射 到数据库 一条数据
            chat_thread = ChatThread(user_id = user_id, title = title)
            # 新增对象，就是插入一条数据
            await self.repository.add(chat_thread)

            return chat_thread