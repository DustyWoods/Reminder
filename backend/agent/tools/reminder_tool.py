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
        
        # 初始化结果日期
        result_dt = ref_dt
        
        # 解析相对时间（日期部分）
        if "明天" in text_lower or "tomorrow" in text_lower:
            result_dt = ref_dt + timedelta(days=1)
        elif "后天" in text_lower or "day after tomorrow" in text_lower:
            result_dt = ref_dt + timedelta(days=2)
        elif "下周" in text_lower or "next week" in text_lower:
            result_dt = ref_dt + timedelta(weeks=1)
        elif "下个月" in text_lower or "next month" in text_lower:
            result_dt = ref_dt + timedelta(days=30)
        elif "今天" not in text_lower and "now" not in text_lower:
            # 尝试直接解析标准格式
            try:
                result_dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    result_dt = datetime.strptime(text, "%Y/%m/%d %H:%M")
                except ValueError:
                    # 保持默认日期（使用ref_dt的日期）
                    pass
        
        # 解析时间部分（小时和分钟）
        # 设置默认时间为0点
        hour = 0
        minute = 0
        
        # 解析中文时间表达
        import re
        
        # 匹配"下午三点"、"晚上八点"、"上午九点"等格式
        time_patterns = [
            r'(上午|早上|早晨)\s*(\d{1,2})[:点时](\d{0,2})',  # 上午/早上 9点/9:30
            r'(下午|中午|午后)\s*(\d{1,2})[:点时](\d{0,2})',  # 下午 3点/3:30
            r'(晚上|夜里|深夜)\s*(\d{1,2})[:点时](\d{0,2})', # 晚上 8点/8:30
            r'(\d{1,2})[:点时](\d{0,2})\s*(上午|早上|早晨)',   # 9点 上午
            r'(\d{1,2})[:点时](\d{0,2})\s*(下午|中午)',       # 3点 下午
            r'(\d{1,2})[:点时](\d{0,2})\s*(晚上|夜里)',       # 8点 晚上
            r'(\d{1,2})[:点时](\d{0,2})',                    # 15:30 或 15点30
        ]
        
        matched = False
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                
                # 判断是12小时制还是24小时制
                period = None
                if "上午" in groups or "早上" in groups or "早晨" in groups:
                    period = "am"
                elif "下午" in groups or "中午" in groups or "午后" in groups:
                    period = "pm"
                elif "晚上" in groups or "夜里" in groups or "深夜" in groups:
                    period = "pm"
                
                # 提取小时和分钟
                nums = [int(g) for g in groups if g.isdigit()]
                if len(nums) >= 1:
                    hour = nums[0]
                if len(nums) >= 2:
                    minute = nums[1]
                
                # 处理12小时制转换
                if period == "pm" and hour < 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                
                matched = True
                break
        
        # 如果没有匹配到时间，尝试简单数字匹配
        if not matched:
            # 匹配单独的数字（如"三点"、"八点"）
            num_match = re.search(r'(\d{1,2})\s*点', text_lower)
            if num_match:
                hour = int(num_match.group(1))
                # 默认"点"在中文语境中通常指下午或晚上（除了明确是上午的情况）
                if "上午" not in text_lower and "早上" not in text_lower:
                    if hour < 12:
                        hour += 12
        
        # 设置时间
        result_dt = result_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        logger.info(f"Parsed datetime result: {result_dt}")
        return result_dt.strftime("%Y-%m-%d %H:%M")


# 以下工具已弃用，不再自动注册（任务提取由 LLM 直接完成，无需这些中间工具）
# 保留代码以备参考
