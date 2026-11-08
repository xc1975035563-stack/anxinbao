from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek

from app.core.config import settings
from app.modules.chat.exceptions import ChatModelNotConfiguredError
from app.modules.chat.models import ChatMessage

SYSTEM_PROMPT = """你是「安心保」智能顾问，用简体中文回答保险咨询。
根据用户的年龄、职业、预算和关注的保障类型，给出清晰、克制的建议。
不要编造未在产品列表中出现的具体产品和价格。产品列表为空时，只做通用说明，并提示用户以实际条款为准。
用户如果是在确认或取消保存方案，只需简短说明已记录该选择，不要声称方案已经写入保单系统。"""

FALLBACK_REPLY = "模型暂时无法回复，请稍后再试。"


def ensure_model_configured() -> None:
    api_key = (settings.llm.api_key or "").strip()
    if not api_key or api_key == "your_deepseek_api_key":
        raise ChatModelNotConfiguredError


async def stream_reply(
    history: list[ChatMessage],
    catalog: str,
) -> AsyncIterator[str]:
    ensure_model_configured()
    model = ChatDeepSeek(
        model=settings.llm.chat_model,
        api_key=settings.llm.api_key,
        temperature=0.3,
    )
    prompt = SYSTEM_PROMPT
    if catalog:
        prompt = f"{prompt}\n\n{catalog}"
    messages: list = [SystemMessage(content=prompt)]
    for item in history:
        if item.role == "user":
            messages.append(HumanMessage(content=item.content))
        elif item.content:
            messages.append(AIMessage(content=item.content))

    async for chunk in model.astream(messages):
        text = _chunk_text(chunk)
        if text:
            yield text


def _chunk_text(chunk: object) -> str:
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
        return "".join(parts)
    text = getattr(chunk, "text", "")
    return text if isinstance(text, str) else ""
