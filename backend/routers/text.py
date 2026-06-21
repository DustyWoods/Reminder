"""
文本任务处理路由 - ReAct Agent 版

统一响应格式：
{
    "success": true/false,
    "summary": "操作结果总结",
    "operation": "create/update/delete/query/mixed",
    "tasks": [...],
    "results": [...]
}
"""
from fastapi import APIRouter, HTTPException, Query

from models import ReminderRequest
from agent import run_react_agent
from utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/text", tags=["text"])


@router.post("", summary="智能任务处理接口（ReAct）")
async def process_text_task(request: ReminderRequest, user_id: int = Query(1)):
    """
    智能任务处理 - 基于 ReAct 框架

    支持多操作组合输入：
    - "下午三点开会，删除遛狗提醒" → 创建+删除
    - "把会议改到明天，取消学习计划" → 更新+删除
    - "今天有什么任务" → 查询

    示例请求: POST /api/text?user_id=1  {"text": "下午三点开会"}
    """
    logger.info(f"Text task from user {user_id}: {request.text}")

    try:
        result = await run_react_agent(request.text, user_id=user_id)
        return _build_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/query", summary="查询任务")
async def query_text_task(user_id: int = Query(1)):
    """查询用户任务"""
    try:
        result = await run_react_agent("查询任务", user_id=user_id)
        return _build_response(result)
    except Exception as e:
        logger.exception(f"Error querying tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_response(result: dict) -> dict:
    """构建统一响应格式"""
    return {
        "success": result.get("success", False),
        "summary": result.get("summary", ""),
        "operation": result.get("operation", "create"),
        "tasks": result.get("tasks", []),
        "results": result.get("results", [])
    }