"""
智能体基类
"""
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from langchain_openai import ChatOpenAI

from agent.config import AgentConfig, get_config
from utils import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    智能体基类
    
    所有智能体都应该继承此类并实现抽象方法
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        version: Optional[str] = None,
        llm: Optional[ChatOpenAI] = None,
        config: Optional[AgentConfig] = None
    ):
        """
        初始化智能体
        
        Args:
            name: 智能体名称
            version: 智能体版本
            llm: LLM 实例
            config: 配置对象
        """
        self.config = config or get_config()
        self.name = name or self.config.agent_name
        self.version = version or self.config.agent_version
        self.llm = llm or self._create_llm()
        self._initialized = False
        
        logger.info(f"Initialized agent: {self.name} v{self.version}")
    
    def _create_llm(self) -> ChatOpenAI:
        """
        创建 LLM 实例
        
        Returns:
            ChatOpenAI: LLM 实例
        """
        return ChatOpenAI(
            model=self.config.effective_model,
            api_key=self.config.effective_api_key,
            base_url=self.config.effective_base_url,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
    
    @abstractmethod
    def invoke(self, input_data: Any, **kwargs) -> Any:
        """
        同步执行智能体
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            Any: 执行结果
        """
        pass
    
    @abstractmethod
    async def ainvoke(self, input_data: Any, **kwargs) -> Any:
        """
        异步执行智能体
        
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            Any: 执行结果
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查智能体是否可用
        
        Returns:
            bool: 是否可用
        """
        return self.llm is not None and self._initialized
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取智能体信息
        
        Returns:
            Dict: 智能体信息
        """
        return {
            "name": self.name,
            "version": self.version,
            "available": self.is_available(),
            "model": self.config.llm_model,
            "provider": self.config.llm_provider.value
        }
