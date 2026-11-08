from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat_thread.exceptions import ChatThreadNotFoundError
from app.modules.chat_thread.repository import ChatThreadRepository
from app.modules.product.repository import ProductRepository

from .exceptions import ChatInputError
from .models import ChatMessage
from .repository import ChatMessageRepository
from .schemas import ChatHistoryResponse, ChatMessageResponse

HISTORY_LIMIT = 20


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.threads = ChatThreadRepository(session)
        self.messages = ChatMessageRepository(session)
        self.products = ProductRepository(session)

    async def history(self, thread_id: UUID, user_id: int) -> ChatHistoryResponse:
        async with self.session.begin():
            await self._require_thread(thread_id, user_id)
            rows = await self.messages.list_by_thread(thread_id)
        return ChatHistoryResponse(
            thread_id=thread_id,
            messages=[self._to_response(row) for row in rows],
        )

    async def begin_turn(
        self,
        thread_id: UUID,
        user_id: int,
        message: str | None,
        decision: dict | None,
    ) -> tuple[list[ChatMessage], str]:
        content = self._user_content(message, decision)
        async with self.session.begin():
            thread = await self._require_thread(thread_id, user_id)
            self.messages.add(
                ChatMessage(thread_id=thread_id, role="user", content=content)
            )
            thread.updated_at = datetime.now(timezone.utc)
            rows = await self.messages.list_by_thread(thread_id)
            catalog = await self._product_catalog()
        return rows[-HISTORY_LIMIT:], catalog

    async def save_assistant(
        self,
        thread_id: UUID,
        user_id: int,
        content: str,
    ) -> None:
        async with self.session.begin():
            thread = await self._require_thread(thread_id, user_id)
            self.messages.add(
                ChatMessage(thread_id=thread_id, role="assistant", content=content)
            )
            thread.updated_at = datetime.now(timezone.utc)

    async def _require_thread(self, thread_id: UUID, user_id: int):
        thread = await self.threads.find_owned(thread_id, user_id)
        if thread is None:
            raise ChatThreadNotFoundError
        return thread

    async def _product_catalog(self) -> str:
        try:
            products = await self.products.find_by_category(None)
        except Exception:
            return ""
        lines = []
        for product in products[:12]:
            premium = product.min_premium
            premium_text = f"{premium}元起" if premium is not None else "保费待定"
            description = (product.description or "").strip().replace("\n", " ")
            if len(description) > 80:
                description = description[:80] + "…"
            lines.append(
                f"- {product.name}｜{product.category}｜{product.insurer}｜{premium_text}｜{description}"
            )
        if not lines:
            return ""
        return "可参考的在售产品：\n" + "\n".join(lines)

    @staticmethod
    def _user_content(message: str | None, decision: dict | None) -> str:
        text = (message or "").strip()
        if text:
            return text
        if not decision:
            raise ChatInputError()
        action = decision.get("action")
        if action == "approve":
            return "确认保存保险方案"
        if action == "reject":
            reason = str(decision.get("reject_reason") or "用户未填写原因").strip()
            return f"取消保存保险方案：{reason}"
        raise ChatInputError("无法识别的确认操作")

    @staticmethod
    def _to_response(row: ChatMessage) -> ChatMessageResponse:
        role = row.role if row.role in ("user", "assistant") else "assistant"
        return ChatMessageResponse(
            role=role,
            content=row.content,
            additional_info=row.additional_info,
        )
