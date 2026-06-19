"""
Agent 模块 - 精简版

基于 LangChain 的智能体模块
- config: 全局配置管理
- tools: 数据库操作工具
- chains: 任务提取链
- agents: 智能体定义
"""

from agent.config import get_config, AgentConfig
from agent.agents import TaskAgent, get_task_agent, task_agent
from agent.tools import get_tool_registry

__version__ = "2.0.0"

__all__ = [
    "get_config", "AgentConfig",
    "TaskAgent", "get_task_agent", "task_agent",
    "get_tool_registry",
]