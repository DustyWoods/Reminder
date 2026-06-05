from fastapi import APIRouter, HTTPException

from models import TaskUpdateRequest, TaskDeleteRequest, TaskResponse, TaskListResponse
from utils import get_logger, get_tasks_by_user_id, update_task, delete_task

logger = get_logger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{user_id}", response_model=TaskListResponse)
async def get_tasks(user_id: int):
    """
    获取用户的任务列表

    登录成功后调用此接口获取用户的所有任务
    """
    logger.info(f"Fetching tasks for user {user_id}")
    
    try:
        tasks = get_tasks_by_user_id(user_id)
        
        # 转换任务数据格式
        task_responses = []
        for task in tasks:
            task_responses.append(TaskResponse(
                id=task['id'],
                user_id=task['user_id'],
                title=task['title'],
                due_date=task['due_date'],
                description=task['description'],
                completed=bool(task['completed']),
                created_at=str(task['created_at'])
            ))
        
        logger.info(f"Found {len(task_responses)} tasks for user {user_id}")
        
        return TaskListResponse(
            success=True,
            message="任务列表获取成功",
            tasks=task_responses
        )
    except Exception as e:
        logger.exception(f"Error fetching tasks for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{user_id}/{task_id}")
async def update_task_status(user_id: int, task_id: int, request: TaskUpdateRequest):
    """
    更新任务信息

    可以更新任务的标题、截止日期、描述和完成状态
    """
    logger.info(f"Updating task {task_id} for user {user_id}")
    
    try:
        # 构建更新参数
        update_data = {}
        if request.title is not None:
            update_data['title'] = request.title
        if request.due_date is not None:
            update_data['due_date'] = request.due_date
        if request.description is not None:
            update_data['description'] = request.description
        if request.completed is not None:
            update_data['completed'] = request.completed
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")
        
        success = update_task(task_id, user_id, **update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无权访问")
        
        logger.info(f"Task {task_id} updated successfully")
        
        return {
            "success": True,
            "message": "任务更新成功"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error updating task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{user_id}/{task_id}")
async def delete_task_by_id(user_id: int, task_id: int):
    """
    删除指定任务
    """
    logger.info(f"Deleting task {task_id} for user {user_id}")
    
    try:
        success = delete_task(task_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无权访问")
        
        logger.info(f"Task {task_id} deleted successfully")
        
        return {
            "success": True,
            "message": "任务删除成功"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error deleting task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")