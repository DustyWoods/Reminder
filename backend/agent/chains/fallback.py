"""
备用链
"""
from typing import List
from datetime import datetime

from models import ReminderResponse
from agent.config import get_config
from utils import get_logger

logger = get_logger(__name__)


class FallbackChain:
    """备用链 - 当主要任务提取失败时使用的备用方案"""

    def __init__(self):
        self.config = get_config()

    def invoke(self, text: str) -> List[ReminderResponse]:
        """将原始文本作为单个任务返回"""
        logger.warning(f"Using fallback chain for: {text[:50]}...")

        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        due_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        return [ReminderResponse(
            title=title,
            due_date=due_date,
            description=text
        )]

    async def ainvoke(self, text: str) -> List[ReminderResponse]:
        """异步执行备用处理"""
        return self.invoke(text)
