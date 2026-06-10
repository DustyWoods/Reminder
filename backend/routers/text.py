"""
文本任务处理路由 - 精简版

统一响应格式：
{
    "session_id": "uuid",
    "text": "用户输入",
    "is_final": true,
    "operation": "create/update/delete/query",
    "success": true/false,
    "message": "操作结果消息",
    "tasks": [...]
}
"""
from fastapi import APIRouter, HTTPException, Query
import uuid

from models import ReminderRequest
from agent import get_task_agent
from utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/text", tags=["text"])


@router.post("", summary="智能任务处理接口")
async def process_text_task(request: ReminderRequest, user_id: int = Query(1)):
    """
    智能任务处理 - 自动识别操作类型（create/update/delete/query）

    示例请求: POST /api/text?user_id=1  {"text": "下午三点开会"}
    """
    logger.info(f"Text task from user {user_id}: {request.text}")

    try:
        task_agent = get_task_agent()
        result = await task_agent.process(request.text, user_id=user_id)
        return _build_response(request.text, result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/create", summary="创建任务")
async def create_text_task(request: ReminderRequest, user_id: int = Query(1)):
    """创建任务"""
    try:
        task_agent = get_task_agent()
        reminders = await task_agent.ainvoke(request.text)
        result = task_agent._do_create(reminders, user_id)
        return _build_response(request.text, result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", summary="查询任务")
async def query_text_task(user_id: int = Query(1)):
    """查询用户任务"""
    try:
        task_agent = get_task_agent()
        result = task_agent._do_query(user_id)
        return _build_response("查询任务", result)
    except Exception as e:
        logger.exception(f"Error querying tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_response(text: str, result: dict) -> dict:
    """构建统一响应格式"""
    return {
        "session_id": str(uuid.uuid4()),
        "text": text,
        "is_final": True,
        "operation": result.get("operation", "create"),
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "tasks": result.get("tasks", [])
    }