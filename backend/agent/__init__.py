"""
Agent 模块

基于 LangChain 和 LangGraph 重构的智能体模块
包含：
- config: 全局配置管理
- tools: 自定义工具
- chains: 业务逻辑链
- graphs: LangGraph 工作流
- agents: 智能体定义
"""

from agent.config import get_config, validate_config, AgentConfig
from agent.agents import TaskAgent, get_task_agent, task_agent
from agent.tools import get_tool_registry
from agent.graphs import create_task_workflow

__version__ = "1.0.0"

__all__ = [
    # 配置
    "get_config",
    "validate_config",
    "AgentConfig",
    
    # 智能体
    "TaskAgent",
    "get_task_agent",
    "task_agent",
    
    # 工具
    "get_tool_registry",
    "tool_registry",
    
    # 工作流
    "create_task_workflow",
]
