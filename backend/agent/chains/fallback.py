"""
备用链
"""
from typing import Optional
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

from models import ReminderResponse
from agent.config import get_config
from utils import get_logger

logger = get_logger(__name__)


class FallbackChain:
    """
    备用链
    
    当主要任务提取失败时使用的备用方案
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        初始化备用链
        
        Args:
            llm: LLM 实例（可选）
        """
        self.config = get_config()
        self.llm = llm or self._create_llm()
        self.chain = self._build_chain()
    
    def _create_llm(self) -> ChatOpenAI:
        """创建 LLM 实例"""
        return ChatOpenAI(
            model=self.config.effective_model,
            api_key=self.config.effective_api_key,
            base_url=self.config.effective_base_url,
            temperature=0.0,  # 使用更低的温度以获得更稳定的输出
            max_tokens=512
        )
    
    def _build_chain(self) -> RunnableSequence:
        """构建备用链"""
        system_prompt = """
你是一个简单的任务信息提取器。请从用户输入中提取基本信息并返回 JSON 格式。

输出格式：
{{
  "title": "从文本中提取的简短标题",
  "due_date": "YYYY-MM-DD HH:MM 格式",
  "description": "原始输入文本"
}}

如果无法提取具体信息，使用默认值。
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        parser = JsonOutputParser()
        
        chain = prompt | self.llm | parser
        return chain
    
    def invoke(self, text: str) -> ReminderResponse:
        """
        执行备用提取
        
        Args:
            text: 用户输入的文本
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.warning(f"Using fallback chain for: {text[:50]}...")
        
        try:
            result = self.chain.invoke({"input": text})
            
            # 构建默认响应
            title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
            due_date = (datetime.now() + timedelta(hours=self.config.default_due_date_hours)).strftime("%Y-%m-%d %H:%M")
            description = text
            
            # 尝试从结果中提取信息
            if isinstance(result, dict):
                title = result.get("title", title)
                due_date = result.get("due_date", due_date)
                description = result.get("description", description)
            
            return ReminderResponse(
                title=title,
                due_date=due_date,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Fallback chain failed: {str(e)}, using hard fallback")
            return self._hard_fallback(text)
    
    def _hard_fallback(self, text: str) -> ReminderResponse:
        """
        硬备用方案（当 LLM 也失败时使用）
        
        Args:
            text: 用户输入的文本
            
        Returns:
            ReminderResponse: 基础任务信息
        """
        logger.error(f"Using hard fallback for: {text[:50]}...")
        
        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        due_date = (datetime.now() + timedelta(hours=self.config.default_due_date_hours)).strftime("%Y-%m-%d %H:%M")
        description = f"原始输入：{text}"
        
        return ReminderResponse(
            title=title,
            due_date=due_date,
            description=description
        )
    
    async def ainvoke(self, text: str) -> ReminderResponse:
        """
        异步执行备用提取
        
        Args:
            text: 用户输入的文本
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.warning(f"Using async fallback chain for: {text[:50]}...")
        
        try:
            result = await self.chain.ainvoke({"input": text})
            
            title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
            due_date = (datetime.now() + timedelta(hours=self.config.default_due_date_hours)).strftime("%Y-%m-%d %H:%M")
            description = text
            
            if isinstance(result, dict):
                title = result.get("title", title)
                due_date = result.get("due_date", due_date)
                description = result.get("description", description)
            
            return ReminderResponse(
                title=title,
                due_date=due_date,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Async fallback chain failed: {str(e)}")
            return self._hard_fallback(text)
