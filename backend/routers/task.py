"""
任务管理路由 - 精简版

提供 CRUD 接口，响应格式与 text.py 统一：
- GET  /api/tasks/{user_id}         - 获取任务列表
- PUT  /api/tasks/{user_id}/{task_id} - 更新任务
- DELETE /api/tasks/{user_id}/{task_id} - 删除任务
"""
from fastapi import APIRouter, HTTPException

from models import TaskUpdateRequest, TaskResponse, TaskListResponse
from agent import get_task_agent
from utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{user_id}", response_model=TaskListResponse)
async def get_tasks(user_id: int):
    """获取用户任务列表"""
    logger.info(f"Fetching tasks for user {user_id}")

    try:
        task_agent = get_task_agent()
        result = task_agent.execute_query(user_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "获取失败"))

        task_responses = []
        for task in result.get("tasks", []):
            task_responses.append(TaskResponse(
                id=task["id"],
                user_id=task.get("user_id", user_id),
                title=task["title"],
                due_date=task["due_date"],
                description=task.get("description"),
                completed=bool(task.get("completed", False)),
                created_at=str(task.get("created_at", ""))
            ))

        logger.info(f"Found {len(task_responses)} tasks for user {user_id}")
        return TaskListResponse(success=True, message="获取成功", tasks=task_responses)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/{task_id}")
async def update_task_by_id(user_id: int, task_id: int, request: TaskUpdateRequest):
    """更新指定任务"""
    logger.info(f"Updating task {task_id} for user {user_id}")

    try:
        if not any([request.title, request.due_date, request.description, request.completed is not None]):
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        from utils.database import update_task, get_task_by_id

        update_data = {}
        if request.title is not None: update_data["title"] = request.title
        if request.due_date is not None: update_data["due_date"] = request.due_date
        if request.description is not None: update_data["description"] = request.description
        if request.completed is not None: update_data["completed"] = request.completed

        success = update_task(task_id, user_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无权限")

        logger.info(f"Task {task_id} updated")
        return {"success": True, "message": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/{task_id}")
async def delete_task_by_id(user_id: int, task_id: int):
    """删除指定任务"""
    logger.info(f"Deleting task {task_id} for user {user_id}")

    try:
        task_agent = get_task_agent()
        result = task_agent.execute_delete(user_id, task_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "删除失败"))

        logger.info(f"Task {task_id} deleted")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))