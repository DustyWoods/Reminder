"""
提醒任务相关工具
"""
from typing import Type, List
from datetime import datetime, timedelta
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from models import ReminderResponse, ReminderListResponse
from .base import BaseCustomTool, tool_registry
from agent.config import get_config
from utils import get_logger

logger = get_logger(__name__)


class CreateReminderInput(BaseModel):
    """创建提醒任务的输入参数"""
    
    title: str = Field(description="任务的简短标题")
    due_date: str = Field(description="任务的截止日期和时间，格式为 YYYY-MM-DD HH:MM")
    description: str = Field(description="任务的详细描述，包含所有相关细节")


class CreateReminderTool(BaseCustomTool):
    """
    创建提醒任务工具
    
    从自然语言中分析并提取提醒任务信息
    """
    
    name: str = "create_reminder"
    description: str = "从自然语言中分析并提取提醒任务信息，创建结构化的任务对象"
    args_schema: Type[BaseModel] = CreateReminderInput
    
    def _run(self, title: str, due_date: str, description: str) -> ReminderResponse:
        """
        执行工具，创建提醒任务
        
        Args:
            title: 任务标题
            due_date: 截止日期和时间（YYYY-MM-DD HH:MM）
            description: 任务描述
            
        Returns:
            ReminderResponse: 结构化的任务信息
        """
        logger.info(f"Creating reminder: {title}")
        
        # 验证标题长度
        config = get_config()
        if len(title) > config.max_title_length:
            title = title[:config.max_title_length]
            logger.warning(f"Title truncated to {config.max_title_length} characters")
        
        # 验证日期格式
        try:
            datetime.strptime(due_date, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(f"Invalid date format: {due_date}. Expected YYYY-MM-DD HH:MM")
        
        return ReminderResponse(
            title=title,
            due_date=due_date,
            description=description
        )


class CreateRemindersInput(BaseModel):
    """批量创建提醒任务的输入参数"""
    
    tasks: List[dict] = Field(description="任务列表，每个任务包含 title、due_date 和 description")


class CreateRemindersTool(BaseCustomTool):
    """
    批量创建提醒任务工具
    
    从自然语言中分析并提取多个提醒任务信息
    """
    
    name: str = "create_reminders"
    description: str = "从自然语言中分析并提取多个提醒任务信息，批量创建结构化的任务对象"
    args_schema: Type[BaseModel] = CreateRemindersInput
    
    def _run(self, tasks: List[dict]) -> ReminderListResponse:
        """
        执行工具，批量创建提醒任务
        
        Args:
            tasks: 任务列表，每个任务包含 title、due_date 和 description
            
        Returns:
            ReminderListResponse: 结构化的任务列表信息
        """
        logger.info(f"Creating {len(tasks)} reminders")
        
        config = get_config()
        result_tasks = []
        
        for task_data in tasks:
            title = task_data.get("title", "")
            due_date = task_data.get("due_date", "")
            description = task_data.get("description", "")
            
            # 验证标题长度
            if len(title) > config.max_title_length:
                title = title[:config.max_title_length]
            
            # 验证日期格式
            try:
                datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            except ValueError:
                # 使用默认日期
                due_date = (datetime.now() + timedelta(hours=config.default_due_date_hours)).strftime("%Y-%m-%d %H:%M")
                logger.warning(f"Invalid date format, using default: {due_date}")
            
            result_tasks.append(ReminderResponse(
                title=title,
                due_date=due_date,
                description=description
            ))
        
        return ReminderListResponse(tasks=result_tasks)


class DateTimeParserInput(BaseModel):
    """日期时间解析输入"""
    
    text: str = Field(description="包含日期时间信息的文本")
    reference_time: str = Field(default=None, description="参考时间（可选），格式为 YYYY-MM-DD HH:MM")


class DateTimeParserTool(BaseCustomTool):
    """
    日期时间解析工具
    
    从自然语言中提取和解析日期时间信息
    """
    
    name: str = "parse_datetime"
    description: str = "从自然语言文本中解析日期时间，支持相对时间表达（如'明天'、'下周'等）"
    args_schema: Type[BaseModel] = DateTimeParserInput
    
    def _run(self, text: str, reference_time: str = None) -> str:
        """
        解析日期时间
        
        Args:
            text: 包含日期时间信息的文本
            reference_time: 参考时间（可选）
            
        Returns:
            str: 解析后的日期时间（YYYY-MM-DD HH:MM 格式）
        """
        logger.info(f"Parsing datetime from: {text}")
        
        # 设置参考时间
        if reference_time:
            ref_dt = datetime.strptime(reference_time, "%Y-%m-%d %H:%M")
        else:
            ref_dt = datetime.now()
        
        # 简单的中文日期时间解析（可扩展）
        text_lower = text.lower()
        
        # 解析相对时间
        if "今天" in text_lower or "now" in text_lower:
            result_dt = ref_dt
        elif "明天" in text_lower or "tomorrow" in text_lower:
            result_dt = ref_dt + timedelta(days=1)
        elif "后天" in text_lower or "day after tomorrow" in text_lower:
            result_dt = ref_dt + timedelta(days=2)
        elif "下周" in text_lower or "next week" in text_lower:
            result_dt = ref_dt + timedelta(weeks=1)
        elif "下个月" in text_lower or "next month" in text_lower:
            result_dt = ref_dt + timedelta(days=30)
        else:
            # 尝试直接解析标准格式
            try:
                result_dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    result_dt = datetime.strptime(text, "%Y/%m/%d %H:%M")
                except ValueError:
                    # 使用默认时间
                    config = get_config()
                    result_dt = ref_dt + timedelta(hours=config.default_due_date_hours)
                    logger.warning(f"Could not parse datetime, using default: {result_dt}")
        
        return result_dt.strftime("%Y-%m-%d %H:%M")


# 注册默认工具
tool_registry.register_tool(CreateReminderTool())
tool_registry.register_tool(CreateRemindersTool())
tool_registry.register_tool(DateTimeParserTool())

logger.info(f"Registered {len(tool_registry)} default tools")
