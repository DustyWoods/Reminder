from fastapi import APIRouter, HTTPException
import uuid
from typing import List

from models import ReminderRequest, ReminderResponse
from agent import get_task_agent
from utils import get_logger, create_task

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["text"])


@router.post("/text")
async def create_text_task(request: ReminderRequest, user_id: int):
    """
    文本任务创建接口

    接收文本，使用 LLM 提取任务信息并保存到数据库，支持多任务提取
    """
    logger.info(f"Received text task request from user {user_id}: {request.text}")

    try:
        task_agent = get_task_agent()
        # agent 内部会自动处理 LLM 不可用的情况
        reminders = task_agent.invoke(request.text)
        logger.info(f"Successfully extracted {len(reminders)} task(s)")
        
        # 处理多个任务
        saved_tasks = []
        for reminder in reminders:
            # 获取任务数据（支持字典和对象两种格式）
            if isinstance(reminder, dict):
                title = reminder["title"]
                due_date = reminder["due_date"]
                description = reminder["description"]
            elif isinstance(reminder, ReminderResponse):
                title = reminder.title
                due_date = reminder.due_date
                description = reminder.description
            else:
                continue
            
            # 保存任务到数据库
            task_id = create_task(
                user_id=user_id,
                title=title,
                due_date=due_date,
                description=description
            )
            
            logger.info(f"Task saved to database with id: {task_id}")
            
            saved_tasks.append({
                "id": task_id,
                "title": title,
                "due_date": due_date,
                "description": description,
                "completed": False
            })
        
        # 返回符合前端期望的数据结构（支持多任务）
        return {
            "session_id": str(uuid.uuid4()),
            "text": request.text,
            "is_final": True,
            "tasks": saved_tasks
        }
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
