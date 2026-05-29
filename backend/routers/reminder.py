from fastapi import APIRouter, HTTPException

from models import ReminderRequest, ReminderResponse
from services import llm_service
from utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["reminder"])


@router.post("/reminder", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest) -> ReminderResponse:
    """
    文本任务创建接口

    接收文本，使用 LLM 提取任务信息并返回
    """
    logger.info(f"Received reminder request: {request.text}")

    if not llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM service not available")

    try:
        reminder = llm_service.extract_reminder(request.text)
        return reminder
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
