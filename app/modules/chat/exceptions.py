from app.core.exceptions import ApplicationError


class ChatInputError(ApplicationError):
    """发送内容为空"""

    status_code = 400
    code = "CHAT_INPUT_INVALID"
    message = "请输入消息内容"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)


class ChatModelNotConfiguredError(ApplicationError):
    """未配置可用的对话模型"""

    status_code = 503
    code = "CHAT_MODEL_NOT_CONFIGURED"
    message = "对话模型未配置，请在 .env 中设置有效的 DEEPSEEK_API_KEY"
