from app.modules.chat_thread.router import router as chat_thread_router
from fastapi import FastAPI
from app.modules.product.router import router as product_router

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
import uvicorn
from contextlib import asynccontextmanager

# 初始化日志系统
configure_logging(settings.logging.level)
logger = get_logger(__name__)


# 生命周期管理（预留）
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"【{settings.app.name}】应用启动中...")
    from app.infra.database import check_database, close_database
    try:
        await check_database()
        yield
    finally:
        logger.info("应用关闭中... ")
        await close_database()
app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
    lifespan=lifespan
)

# 创建 app 后注册路由
app.include_router(product_router)

app.include_router(chat_thread_router)

@app.get("/health", summary="健康检测接口")
async def health_check() -> dict[str, str]:
    logger.info("执行健康检查")
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=False
    )