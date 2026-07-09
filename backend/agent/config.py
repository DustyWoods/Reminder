"""
Agent 模块配置管理
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


class AgentConfig(BaseSettings):
    """Agent 配置"""

    # LLM 配置
    llm_provider: LLMProvider = LLMProvider.DEEPSEEK
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # API 密钥
    agent_llm_api_key: Optional[str] = None
    agent_llm_base_url: Optional[str] = None
    agent_llm_model: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    deepseek_model: Optional[str] = None

    # Agent 配置
    agent_name: str = "task_assistant"
    agent_version: str = "4.0.0"

    # LangGraph 配置
    graph_recursion_limit: int = 50

    # 业务配置
    max_title_length: int = 10

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_prefix = ""
        extra = "ignore"

    @property
    def effective_api_key(self) -> Optional[str]:
        return self.agent_llm_api_key or self.deepseek_api_key

    @property
    def effective_base_url(self) -> Optional[str]:
        return self.agent_llm_base_url or self.deepseek_base_url

    @property
    def effective_model(self) -> str:
        return self.agent_llm_model or self.llm_model or self.deepseek_model or "deepseek-chat"


config = AgentConfig()


def get_config() -> AgentConfig:
    return config