"""
任务助手智能体 - 优化版

核心优化：
1. 简化代理结构，减少重复代码
2. 统一任务提取流程，优先使用LLM处理
3. 优化错误处理和日志记录
"""
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from models import ReminderResponse
from agent.config import AgentConfig, get_config, validate_config
from agent.agents.base import BaseAgent
from agent.graphs import create_task_workflow
from agent.chains import TaskExtractionChain, FallbackChain
from datetime import datetime
from agent.tools import get_tool_registry
from utils import get_logger

logger = get_logger(__name__)


class TaskAgent(BaseAgent):
    """
    任务助手智能体
    
    整合LangGraph工作流、业务链和工具，提供完整的任务提取功能
    
    核心特性：
    - 智能多任务识别：准确识别自然语言中的多个任务
    - 智能时间分析：结合上下文准确解析时间
    - 简练标题生成：生成包含核心动宾结构的简洁标题
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
            llm: LLM实例
            config: 配置对象
        """
        super().__init__(name=name, version=version, llm=llm, config=config)
        
        # 初始化工具
        self.tool_registry = get_tool_registry()
        logger.info(f"Loaded {len(self.tool_registry)} tools")
        
        # 初始化业务链（核心任务提取）
        self.extraction_chain = TaskExtractionChain(llm=self.llm)
        self.fallback_chain = FallbackChain(llm=self.llm)
        
        self._initialized = True
        logger.info(f"TaskAgent '{name}' v{version} initialized")
    
    def invoke(
        self,
        text: str,
        use_workflow: bool = False,
        use_fallback: bool = True,
        **kwargs
    ) -> List[ReminderResponse]:
        """
        执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            use_workflow: 是否使用LangGraph工作流（默认关闭，优先使用直连链）
            use_fallback: 是否启用备用方案
            **kwargs: 额外参数
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info(f"TaskAgent processing: {text[:50]}...")
        
        if not self.is_available():
            logger.warning("TaskAgent not available, using hard fallback")
            return self._hard_fallback(text)
        
        try:
            if use_workflow:
                # 使用LangGraph工作流（可选）
                result = self._invoke_workflow(text, **kwargs)
            else:
                # 优先使用直连链（简化流程，减少中间环节）
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
        use_workflow: bool = False,
        use_fallback: bool = True,
        **kwargs
    ) -> List[ReminderResponse]:
        """
        异步执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            use_workflow: 是否使用LangGraph工作流（默认关闭，优先使用直连链）
            use_fallback: 是否启用备用方案
            **kwargs: 额外参数
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info(f"TaskAgent async processing: {text[:50]}...")
        
        if not self.is_available():
            logger.warning("TaskAgent not available, using hard fallback")
            return self._hard_fallback(text)
        
        try:
            if use_workflow:
                # 使用LangGraph工作流（可选）
                result = await self._ainvoke_workflow(text, **kwargs)
            else:
                # 优先使用直连链（简化流程，减少中间环节）
                result = await self._ainvoke_chain(text, **kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"Async task extraction failed: {str(e)}")
            
            if use_fallback and self.config.enable_fallback:
                logger.warning("Using async fallback chain")
                return await self.fallback_chain.ainvoke(text)
            else:
                return self._hard_fallback(text)
    
    def _invoke_workflow(self, text: str, **kwargs) -> List[ReminderResponse]:
        """
        使用LangGraph工作流执行
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info("Using LangGraph workflow")
        
        # 创建工作流（按需创建，避免初始化时的性能开销）
        workflow = create_task_workflow(llm=self.llm)
        
        # 确保传递必要的配置参数
        config = kwargs.get('config', {'configurable': {'thread_id': 'task_agent_thread'}})
        result = workflow.invoke(text, config=config)
        
        # 解析工作流结果
        if result.get("task_extracted"):
            workflow_result = result.get("result", {})
            
            if isinstance(workflow_result, list):
                return [ReminderResponse(**task) for task in workflow_result]
            
            if isinstance(workflow_result, ReminderResponse):
                return [workflow_result]
            
            if isinstance(workflow_result, dict):
                # 检查是否有工具返回的字符串格式结果
                content = workflow_result.get("content", "")
                if isinstance(content, str):
                    if content.startswith("tasks=[") and content.endswith("]"):
                        # 解析工具返回的字符串格式结果
                        try:
                            import re
                            pattern = r"ReminderResponse\(title='([^']+)', due_date='([^']+)', description='([^']+)'\)"
                            matches = re.findall(pattern, content)
                            if matches:
                                return [ReminderResponse(title=m[0], due_date=m[1], description=m[2]) for m in matches]
                        except Exception as e:
                            logger.warning(f"Failed to parse tool result: {str(e)}")
                    elif content.startswith("tasks="):
                        # 尝试提取JSON格式的任务列表
                        try:
                            import re
                            import json
                            json_match = re.search(r'tasks=\[(.+)\]', content, re.DOTALL)
                            if json_match:
                                tasks_json = "[" + json_match.group(1) + "]"
                                tasks_list = json.loads(tasks_json)
                                if isinstance(tasks_list, list):
                                    return [ReminderResponse(**task) for task in tasks_list]
                        except Exception as e:
                            logger.warning(f"Failed to parse tool result JSON: {str(e)}")
                
                tasks_data = workflow_result.get("tasks", workflow_result)
                if isinstance(tasks_data, list):
                    return [ReminderResponse(**task) for task in tasks_data]
                else:
                    try:
                        return [ReminderResponse(**workflow_result)]
                    except ValidationError as e:
                        logger.warning(f"Workflow result validation failed: {str(e)}")
        
        # 如果没有有效结果，使用备用链
        if self.config.enable_fallback:
            logger.warning("Workflow did not extract task, using fallback chain")
            return self.fallback_chain.invoke(text)
        
        return self._hard_fallback(text)
    
    async def _ainvoke_workflow(self, text: str, **kwargs) -> List[ReminderResponse]:
        """
        异步使用LangGraph工作流执行
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info("Using async LangGraph workflow")
        
        # 创建工作流（按需创建）
        workflow = create_task_workflow(llm=self.llm)
        
        # 确保传递必要的配置参数
        config = kwargs.get('config', {'configurable': {'thread_id': 'task_agent_thread'}})
        result = await workflow.ainvoke(text, config=config)
        
        if result.get("task_extracted"):
            workflow_result = result.get("result", {})
            
            if isinstance(workflow_result, list):
                return [ReminderResponse(**task) for task in workflow_result]
            
            if isinstance(workflow_result, ReminderResponse):
                return [workflow_result]
            
            if isinstance(workflow_result, dict):
                tasks_data = workflow_result.get("tasks", workflow_result)
                if isinstance(tasks_data, list):
                    return [ReminderResponse(**task) for task in tasks_data]
                else:
                    try:
                        return [ReminderResponse(**workflow_result)]
                    except ValidationError as e:
                        logger.warning(f"Async workflow result validation failed: {str(e)}")
        
        if self.config.enable_fallback:
            logger.warning("Async workflow did not extract task, using fallback chain")
            return await self.fallback_chain.ainvoke(text)
        
        return self._hard_fallback(text)
    
    def _invoke_chain(self, text: str, **kwargs) -> List[ReminderResponse]:
        """
        使用业务链执行（核心路径）
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info("Using extraction chain (primary path)")
        
        try:
            return self.extraction_chain.invoke(text)
        except Exception as e:
            logger.warning(f"Extraction chain failed: {str(e)}")
            
            if self.config.enable_fallback:
                return self.fallback_chain.invoke(text)
            
            return self._hard_fallback(text)
    
    async def _ainvoke_chain(self, text: str, **kwargs) -> List[ReminderResponse]:
        """
        异步使用业务链执行（核心路径）
        
        Args:
            text: 用户输入文本
            **kwargs: 额外参数
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info("Using async extraction chain (primary path)")
        
        try:
            return await self.extraction_chain.ainvoke(text)
        except Exception as e:
            logger.warning(f"Async extraction chain failed: {str(e)}")
            
            if self.config.enable_fallback:
                return await self.fallback_chain.ainvoke(text)
            
            return self._hard_fallback(text)
    
    def _hard_fallback(self, text: str) -> List[ReminderResponse]:
        """
        硬备用方案：简单的任务创建（不使用复杂规则）
        
        Args:
            text: 用户输入文本
            
        Returns:
            List[ReminderResponse]: 任务列表
        """
        logger.error(f"Using hard fallback for: {text[:50]}...")
        
        # 简单处理：创建一个包含原始文本的任务
        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        due_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return [ReminderResponse(
            title=title,
            due_date=due_date,
            description=text
        )]
    
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
            "nodes": ["extract", "validate", "tools", "fallback"],
            "checkpointer": self.config.graph_checkpointer,
            "primary_path": "extraction_chain"
        }


# 创建全局任务助手实例
task_agent = TaskAgent()


def get_task_agent() -> TaskAgent:
    """获取全局任务助手实例"""
    return task_agent