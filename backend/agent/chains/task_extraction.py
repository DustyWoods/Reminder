"""
任务提取链
"""
from typing import Optional, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

from models import ReminderResponse
from agent.config import get_config
from utils import get_logger

logger = get_logger(__name__)


class TaskExtractionChain:
    """
    任务提取链
    
    使用 LLM 从自然语言文本中提取任务信息
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        初始化任务提取链
        
        Args:
            llm: LLM 实例（可选，如果不提供则使用配置创建）
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
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
    
    def _build_chain(self) -> RunnableSequence:
        """
        构建任务提取链
        
        Returns:
            RunnableSequence: 可执行的链
        """
        system_prompt = """
你是一个专业的任务提取助手。请从用户输入的自然语言文本中提取任务信息。

要求：
1. 任务标题应该简洁明了，不超过{max_title_length}个字符
2. 截止日期格式必须为 YYYY-MM-DD HH:MM
3. 任务描述应该包含所有相关的细节信息
4. 如果用户没有明确指定截止日期，使用合理的默认时间

请严格按照以下 JSON 格式输出：
{{
  "title": "任务标题",
  "due_date": "YYYY-MM-DD HH:MM",
  "description": "任务描述"
}}
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        # 使用 partial 注入配置参数
        prompt_with_config = prompt.partial(
            max_title_length=str(self.config.max_title_length)
        )
        
        parser = JsonOutputParser(pydantic_object=ReminderResponse)
        
        chain = prompt_with_config | self.llm | parser
        return chain
    
    def invoke(self, text: str) -> ReminderResponse:
        """
        执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info(f"Extracting task from: {text[:50]}...")
        
        try:
            result = self.chain.invoke({"input": text})
            
            if isinstance(result, ReminderResponse):
                return result
            
            if isinstance(result, dict):
                return ReminderResponse(**result)
            
            raise ValueError(f"Unexpected result type: {type(result)}")
            
        except Exception as e:
            logger.error(f"Task extraction failed: {str(e)}")
            raise
    
    async def ainvoke(self, text: str) -> ReminderResponse:
        """
        异步执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info(f"Async extracting task from: {text[:50]}...")
        
        try:
            result = await self.chain.ainvoke({"input": text})
            
            if isinstance(result, ReminderResponse):
                return result
            
            if isinstance(result, dict):
                return ReminderResponse(**result)
            
            raise ValueError(f"Unexpected result type: {type(result)}")
            
        except Exception as e:
            logger.error(f"Async task extraction failed: {str(e)}")
            raise
