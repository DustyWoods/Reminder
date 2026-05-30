from fastapi import APIRouter, HTTPException
import uuid

from models import ReminderRequest
from services import llm_service
from utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["text"])


@router.post("/text")
async def create_text_task(request: ReminderRequest):
    """
    文本任务创建接口

    接收文本，使用 LLM 提取任务信息并返回
    """
    logger.info(f"Received text task request: {request.text}")

    if not llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM service not available")

    try:
        # 调用 LLM 服务提取任务信息
        # reminder = llm_service.extract_reminder(request.text)
        
        # logger.info(f"Successfully extracted reminder: {reminder.title}")
        
        # 返回符合前端期望的数据结构
        # return {
        #     "session_id": str(uuid.uuid4()),
        #     "text": request.text,
        #     "is_final": True,
        #     "task": {
        #         "title": reminder.title,
        #         "due_date": reminder.due_date,
        #         "description": reminder.description
        #     }
        # }
        return {
            "session_id": str(uuid.uuid4()),
            "text": request.text,
            "is_final": True,
            "task": {
                "title": "测试任务",
                "due_date": "2022-12-12 12:00",
                "description": "这是一个测试任务"
            }
        }
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
