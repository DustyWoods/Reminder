from fastapi import APIRouter, HTTPException
import uuid

from models import ReminderRequest
from agent import get_task_agent
from utils import get_logger, create_task

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["text"])


@router.post("/text")
async def create_text_task(request: ReminderRequest, user_id: int):
    """
    文本任务创建接口

    接收文本，使用 LLM 提取任务信息并保存到数据库
    """
    logger.info(f"Received text task request from user {user_id}: {request.text}")

    try:
        task_agent = get_task_agent()
        if task_agent.is_available():
            # 使用新的 invoke 方法
            reminder = task_agent.invoke(request.text)
            logger.info(f"Successfully extracted reminder: {reminder.title}")
        else:
            logger.warning("Task agent not available, using mock data")
            reminder = {
                "title": request.text[:50] if len(request.text) > 50 else request.text,
                "due_date": "2026-06-30 18:00",
                "description": f"任务描述：{request.text}"
            }
        
        # 获取任务数据（支持字典和对象两种格式）
        if isinstance(reminder, dict):
            title = reminder["title"]
            due_date = reminder["due_date"]
            description = reminder["description"]
        else:
            title = reminder.title
            due_date = reminder.due_date
            description = reminder.description
        
        # 保存任务到数据库
        task_id = create_task(
            user_id=user_id,
            title=title,
            due_date=due_date,
            description=description
        )
        
        logger.info(f"Task saved to database with id: {task_id}")
        
        # 返回符合前端期望的数据结构
        return {
            "session_id": str(uuid.uuid4()),
            "text": request.text,
            "is_final": True,
            "task": {
                "id": task_id,
                "title": title,
                "due_date": due_date,
                "description": description,
                "completed": False
            }
        }
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
