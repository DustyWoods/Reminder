"""
任务数据库操作工具

提供对任务数据库的增删改查操作
"""
from typing import Type, Optional
from datetime import datetime
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from utils.database import (
    create_task,
    get_tasks_by_user_id,
    get_task_by_id,
    update_task,
    delete_task
)
from .base import BaseCustomTool, tool_registry
from utils import get_logger

logger = get_logger(__name__)


class CreateTaskInput(BaseModel):
    """创建任务的输入参数"""
    
    user_id: int = Field(description="用户ID")
    title: str = Field(description="任务的简短标题")
    due_date: str = Field(description="任务的截止日期和时间，格式为 YYYY-MM-DD HH:MM")
    description: str = Field(default=None, description="任务的详细描述")


class CreateTaskTool(BaseCustomTool):
    """
    创建任务工具
    
    在数据库中创建新任务
    """
    
    name: str = "create_task"
    description: str = "在数据库中创建新任务，需要用户ID、任务标题、截止日期，可选描述"
    args_schema: Type[BaseModel] = CreateTaskInput
    
    def _run(self, user_id: int, title: str, due_date: str, description: str = None) -> dict:
        """
        执行工具，在数据库中创建任务
        
        Args:
            user_id: 用户ID
            title: 任务标题
            due_date: 截止日期和时间（YYYY-MM-DD HH:MM）
            description: 任务描述（可选）
            
        Returns:
            dict: 创建的任务信息
        """
        logger.info(f"Creating task in database for user {user_id}: {title}")
        
        # 验证日期格式
        try:
            datetime.strptime(due_date, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(f"Invalid date format: {due_date}. Expected YYYY-MM-DD HH:MM")
        
        task_id = create_task(user_id, title, due_date, description)
        
        return {
            "success": True,
            "task_id": task_id,
            "title": title,
            "due_date": due_date,
            "description": description,
            "message": "任务创建成功"
        }


class UpdateTaskInput(BaseModel):
    """更新任务的输入参数"""
    
    task_id: int = Field(description="要更新的任务ID")
    user_id: int = Field(description="用户ID")
    title: str = Field(default=None, description="更新后的任务标题")
    due_date: str = Field(default=None, description="更新后的截止日期，格式为 YYYY-MM-DD HH:MM")
    description: str = Field(default=None, description="更新后的任务描述")
    completed: bool = Field(default=None, description="任务是否完成")


class UpdateTaskTool(BaseCustomTool):
    """
    更新任务工具
    
    更新数据库中已存在的任务信息
    """
    
    name: str = "update_task"
    description: str = "更新数据库中已存在的任务信息，可以更新标题、截止日期、描述或完成状态"
    args_schema: Type[BaseModel] = UpdateTaskInput
    
    def _run(
        self,
        task_id: int,
        user_id: int,
        title: str = None,
        due_date: str = None,
        description: str = None,
        completed: bool = None
    ) -> dict:
        """
        执行工具，更新任务信息
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            title: 更新后的任务标题（可选）
            due_date: 更新后的截止日期（可选）
            description: 更新后的任务描述（可选）
            completed: 更新后的完成状态（可选）
            
        Returns:
            dict: 更新结果
        """
        logger.info(f"Updating task {task_id} for user {user_id}")
        
        # 验证日期格式
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError(f"Invalid date format: {due_date}. Expected YYYY-MM-DD HH:MM")
        
        # 构建更新参数
        update_params = {}
        if title is not None:
            update_params['title'] = title
        if due_date is not None:
            update_params['due_date'] = due_date
        if description is not None:
            update_params['description'] = description
        if completed is not None:
            update_params['completed'] = completed
        
        if not update_params:
            return {"success": False, "message": "没有提供任何更新参数"}
        
        success = update_task(task_id, user_id, **update_params)
        
        if success:
            return {
                "success": True,
                "task_id": task_id,
                "updated_fields": list(update_params.keys()),
                "message": "任务更新成功"
            }
        else:
            return {
                "success": False,
                "task_id": task_id,
                "message": "任务更新失败，任务不存在或无权限"
            }


class DeleteTaskInput(BaseModel):
    """删除任务的输入参数"""
    
    task_id: int = Field(description="要删除的任务ID")
    user_id: int = Field(description="用户ID")


class DeleteTaskTool(BaseCustomTool):
    """
    删除任务工具
    
    从数据库中删除指定任务
    """
    
    name: str = "delete_task"
    description: str = "从数据库中删除指定任务，需要任务ID和用户ID"
    args_schema: Type[BaseModel] = DeleteTaskInput
    
    def _run(self, task_id: int, user_id: int) -> dict:
        """
        执行工具，删除任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            dict: 删除结果
        """
        logger.info(f"Deleting task {task_id} for user {user_id}")
        
        success = delete_task(task_id, user_id)
        
        if success:
            return {
                "success": True,
                "task_id": task_id,
                "message": "任务删除成功"
            }
        else:
            return {
                "success": False,
                "task_id": task_id,
                "message": "任务删除失败，任务不存在或无权限"
            }


class GetTasksInput(BaseModel):
    """查询任务列表的输入参数"""
    
    user_id: int = Field(description="用户ID")


class GetTasksTool(BaseCustomTool):
    """
    查询任务列表工具
    
    获取指定用户的所有任务
    """
    
    name: str = "get_tasks"
    description: str = "获取指定用户的所有任务列表"
    args_schema: Type[BaseModel] = GetTasksInput
    
    def _run(self, user_id: int) -> dict:
        """
        执行工具，获取任务列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 任务列表
        """
        logger.info(f"Getting tasks for user {user_id}")
        
        tasks = get_tasks_by_user_id(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "task_count": len(tasks),
            "tasks": tasks
        }


class GetTaskInput(BaseModel):
    """查询单个任务的输入参数"""
    
    task_id: int = Field(description="任务ID")
    user_id: int = Field(description="用户ID")


class GetTaskTool(BaseCustomTool):
    """
    查询单个任务工具
    
    根据任务ID获取任务详细信息
    """
    
    name: str = "get_task"
    description: str = "根据任务ID获取任务详细信息"
    args_schema: Type[BaseModel] = GetTaskInput
    
    def _run(self, task_id: int, user_id: int) -> dict:
        """
        执行工具，获取任务详情
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            dict: 任务详情
        """
        logger.info(f"Getting task {task_id} for user {user_id}")
        
        task = get_task_by_id(task_id, user_id)
        
        if task:
            return {
                "success": True,
                "task": task
            }
        else:
            return {
                "success": False,
                "task_id": task_id,
                "message": "任务不存在或无权限"
            }


# 注册数据库操作工具
tool_registry.register_tool(CreateTaskTool())
tool_registry.register_tool(UpdateTaskTool())
tool_registry.register_tool(DeleteTaskTool())
tool_registry.register_tool(GetTasksTool())
tool_registry.register_tool(GetTaskTool())

logger.info(f"Registered {len(tool_registry)} database tools")