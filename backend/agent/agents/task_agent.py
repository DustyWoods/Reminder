"""
任务助手智能体
"""
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from models import ReminderResponse
from agent.config import AgentConfig, get_config, validate_config
from agent.agents.base import BaseAgent
from agent.graphs import create_task_workflow
from agent.chains import TaskExtractionChain, FallbackChain
from agent.tools import get_tool_registry
from utils import get_logger

logger = get_logger(__name__)


class TaskAgent(BaseAgent):
    """
    任务助手智能体
    
    整合 LangGraph 工作流、业务链和工具，提供完整的任务提取功能
    """
    
    def __init__(
        self,
        name: str = "task_agent",
        version: str = "1.0.0",
        llm: Optional[ChatOpenAI] = None,
        config: Optional[AgentConfig] = None
    ):
        """
        初始化任务助手智能体
        
        Args:
            name: 智能体名称
            version: 智能体版本
            llm: LLM 实例
            config: 配置对象
        """
        super().__init__(name=name, version=version, llm=llm, config=config)
        
        # 初始化工具
        self.tool_registry = get_tool_registry()
        logger.info(f"Loaded {len(self.tool_registry)} tools")
        
        # 初始化工作流
        self.workflow = create_task_workflow(llm=self.llm)
        
        # 初始化业务链
        self.extraction_chain = TaskExtractionChain(llm=self.llm)
        self.fallback_chain = FallbackChain(llm=self.llm)
        
        self._initialized = True
        logger.info(f"TaskAgent '{name}' fully initialized")
    
    def invoke(
        self,
        text: str,
        use_workflow: bool = True,
        use_fallback: bool = True,
        **kwargs
    ) -> ReminderResponse:
        """
        执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            use_workflow: 是否使用 LangGraph 工作流
            use_fallback: 是否启用备用方案
            **kwargs: 额外参数
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info(f"TaskAgent processing: {text[:50]}...")
        
        if not self.is_available():
            logger.warning("TaskAgent not available, using hard fallback")
            return self._hard_fallback(text)
        
        try:
            if use_workflow:
                # 使用 LangGraph 工作流
                result = self._invoke_workflow(text, **kwargs)
            else:
                # 使用业务链
                result = self._invoke_chain(text, **kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"Task extraction failed: {str(e)}")
            
            if use_fallback and self.config.enable_fallback:
                logger.warning("Using fallback chain")
                return self.fallback_chain.invoke(text)
            else:
                return self._hard_fallback(text)
    
    async def ainvoke(
        self,
        text: str,
        use_workflow: bool = True,
        use_fallback: bool = True,
        **kwargs
    ) -> ReminderResponse:
        """
        异步执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            use_workflow: 是否使用 LangGraph 工作流
            use_fallback: 是否启用备用方案
            **kwargs: 额外参数
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info(f"TaskAgent async processing: {text[:50]}...")
        
        if not self.is_available():
            logger.warning("TaskAgent not available, using hard fallback")
            return self._hard_fallback(text)
        
        try:
            if use_workflow:
                # 使用 LangGraph 工作流
                result = await self._ainvoke_workflow(text, **kwargs)
            else:
                # 使用业务链
                result = await self._ainvoke_chain(text, **kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"Async task extraction failed: {str(e)}")
            
            if use_fallback and self.config.enable_fallback:
                logger.warning("Using async fallback chain")
                return await self.fallback_chain.ainvoke(text)
            else:
                return self._hard_fallback(text)
    
    def _invoke_workflow(self, text: str, **kwargs) -> ReminderResponse:
        """
        使用 LangGraph 工作流执行
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info("Using LangGraph workflow")
        
        result = self.workflow.invoke(text, **kwargs)
        
        # 解析工作流结果
        if result.get("task_extracted"):
            workflow_result = result.get("result", {})
            
            if isinstance(workflow_result, ReminderResponse):
                return workflow_result
            
            if isinstance(workflow_result, dict):
                try:
                    return ReminderResponse(**workflow_result)
                except ValidationError as e:
                    logger.warning(f"Workflow result validation failed: {str(e)}")
        
        # 如果没有有效结果，使用备用链
        if self.config.enable_fallback:
            logger.warning("Workflow did not extract task, using fallback chain")
            return self.fallback_chain.invoke(text)
        
        return self._hard_fallback(text)
    
    async def _ainvoke_workflow(self, text: str, **kwargs) -> ReminderResponse:
        """
        异步使用 LangGraph 工作流执行
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info("Using async LangGraph workflow")
        
        result = await self.workflow.ainvoke(text, **kwargs)
        
        if result.get("task_extracted"):
            workflow_result = result.get("result", {})
            
            if isinstance(workflow_result, ReminderResponse):
                return workflow_result
            
            if isinstance(workflow_result, dict):
                try:
                    return ReminderResponse(**workflow_result)
                except ValidationError as e:
                    logger.warning(f"Async workflow result validation failed: {str(e)}")
        
        if self.config.enable_fallback:
            logger.warning("Async workflow did not extract task, using fallback chain")
            return await self.fallback_chain.ainvoke(text)
        
        return self._hard_fallback(text)
    
    def _invoke_chain(self, text: str, **kwargs) -> ReminderResponse:
        """
        使用业务链执行
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info("Using extraction chain")
        
        try:
            return self.extraction_chain.invoke(text)
        except Exception as e:
            logger.warning(f"Extraction chain failed: {str(e)}")
            
            if self.config.enable_fallback:
                return self.fallback_chain.invoke(text)
            
            return self._hard_fallback(text)
    
    async def _ainvoke_chain(self, text: str, **kwargs) -> ReminderResponse:
        """
        异步使用业务链执行
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            ReminderResponse: 提取的任务信息
        """
        logger.info("Using async extraction chain")
        
        try:
            return await self.extraction_chain.ainvoke(text)
        except Exception as e:
            logger.warning(f"Async extraction chain failed: {str(e)}")
            
            if self.config.enable_fallback:
                return await self.fallback_chain.ainvoke(text)
            
            return self._hard_fallback(text)
    
    def _hard_fallback(self, text: str) -> ReminderResponse:
        """
        硬备用方案
        
        Args:
            text: 用户输入文本
            
        Returns:
            ReminderResponse: 基础任务信息
        """
        logger.error(f"Using hard fallback for: {text[:50]}...")
        
        from datetime import datetime, timedelta
        
        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        due_date = (datetime.now() + timedelta(hours=self.config.default_due_date_hours)).strftime("%Y-%m-%d %H:%M")
        description = f"原始输入：{text}"
        
        return ReminderResponse(
            title=title,
            due_date=due_date,
            description=description
        )
    
    def get_tools_info(self) -> Dict[str, Any]:
        """
        获取工具信息
        
        Returns:
            Dict: 工具信息
        """
        return {
            "count": len(self.tool_registry),
            "names": self.tool_registry.get_tool_names()
        }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        获取工作流信息
        
        Returns:
            Dict: 工作流信息
        """
        return {
            "type": "LangGraph",
            "nodes": ["analyze", "extract", "validate", "tools", "fallback"],
            "checkpointer": self.config.graph_checkpointer
        }


# 创建全局任务助手实例
task_agent = TaskAgent()


def get_task_agent() -> TaskAgent:
    """获取全局任务助手实例"""
    return task_agent
