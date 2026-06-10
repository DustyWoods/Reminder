"""
Agent 模块配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from enum import Enum


class LLMProvider(str, Enum):
    """LLM 提供商枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


import os

class AgentConfig(BaseSettings):
    """Agent 配置类"""
    
    # LLM 配置 - 支持多种命名方式
    llm_provider: LLMProvider = LLMProvider.DEEPSEEK
    llm_model: str = "deepseek-chat"
    
    # 支持 DeepSeek 特定配置
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    deepseek_model: Optional[str] = None
    
    # 通用 LLM 配置（支持 AGENT_ 前缀）
    agent_llm_api_key: Optional[str] = None
    agent_llm_base_url: Optional[str] = None
    agent_llm_model: Optional[str] = None
    
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    
    # Agent 配置
    agent_name: str = "task_assistant"
    agent_version: str = "1.0.0"
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # 工具配置
    enable_tools: bool = True
    tool_timeout: int = 30
    
    # LangGraph 配置
    graph_recursion_limit: int = 50
    graph_checkpointer: bool = True
    
    # 业务配置
    default_due_date_hours: int = 24  # 默认截止日期（小时）
    max_title_length: int = 10  # 最大标题长度
    enable_fallback: bool = True  # 启用备用方案
    
    class Config:
        # 从 agent 目录下的 .env 文件读取配置
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_prefix = ""
        extra = "ignore"
    
    @property
    def effective_api_key(self) -> Optional[str]:
        """获取有效的 API 密钥"""
        return self.agent_llm_api_key or self.deepseek_api_key
    
    @property
    def effective_base_url(self) -> Optional[str]:
        """获取有效的 Base URL"""
        return self.agent_llm_base_url or self.deepseek_base_url
    
    @property
    def effective_model(self) -> str:
        """获取有效的模型名称"""
        return self.agent_llm_model or self.llm_model or self.deepseek_model or "deepseek-chat"


# 全局配置实例
config = AgentConfig()


def get_config() -> AgentConfig:
    """获取全局配置实例"""
    return config


def validate_config() -> bool:
    """验证配置是否完整"""
    if not config.effective_api_key:
        return False
    if config.effective_api_key == "your_api_key_here":
        return False
    return True
