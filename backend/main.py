import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from config import settings
from utils import setup_logging, get_logger
from routers import text_router, voice_router, auth_router, task_router
from services import SHERPA_AVAILABLE

# 加载环境变量
load_dotenv()

# 配置日志
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Reminder Backend API...")
    logger.info(f"ASR Available: {SHERPA_AVAILABLE}")
    logger.info(f"LLM API Key configured: {bool(settings.deepseek_api_key and settings.deepseek_api_key != 'your_api_key_here')}")

    # 确保 assets 目录存在
    os.makedirs("assets/models/zipformer", exist_ok=True)

    yield

    # 关闭时
    logger.info("Shutting down Reminder Backend API...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Reminder Backend",
    version="1.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(auth_router)
app.include_router(text_router)
app.include_router(voice_router)
app.include_router(task_router)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "Reminder Backend API is running"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "asr_available": SHERPA_AVAILABLE,
        "llm_available": bool(settings.deepseek_api_key and settings.deepseek_api_key != "your_api_key_here")
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )