"""
备用链
"""
from typing import Optional, List
from datetime import datetime

from models import ReminderResponse
from agent.config import get_config
from utils import get_logger

logger = get_logger(__name__)


class FallbackChain:
    """
    备用链
    
    当主要任务提取失败时使用的备用方案，使用简单处理
    
    注意：此类仅用于任务提取，不负责数据库保存。
    数据库保存由调用方（如 TaskAgent）负责。
    """
    
    def __init__(self, llm: Optional = None):
        """
        初始化备用链
        
        Args:
            llm: LLM 实例（可选，不再使用）
        """
        self.config = get_config()
        # 不再使用 LLM，直接返回简单结果
    
    def invoke(self, text: str) -> List[ReminderResponse]:
        """
        执行备用处理
        
        Args:
            text: 用户输入文本
            
        Returns:
            List[ReminderResponse]: 任务列表（仅包含任务信息，不含数据库ID）
        """
        logger.warning(f"Using fallback chain for: {text[:50]}...")
        
        # 简单处理：创建一个包含原始文本的任务
        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        due_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return [ReminderResponse(
            title=title,
            due_date=due_date,
            description=text
        )]
    
    async def ainvoke(self, text: str) -> List[ReminderResponse]:
        """
        异步执行备用处理
        
        Args:
            text: 用户输入文本
            
        Returns:
            List[ReminderResponse]: 任务列表（仅包含任务信息，不含数据库ID）
        """
        return self.invoke(text)
