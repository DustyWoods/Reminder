"""
Agent 模块 - ReAct 版

基于 LangGraph 的 ReAct 框架智能体
流程: Plan → Act → Observe → Summarize
"""
from agent.config import get_config, AgentConfig
from agent.graph import create_react_agent, run_react_agent
from agent.state import AgentState

__version__ = "4.0.0"

__all__ = [
    "get_config",
    "AgentConfig",
    "create_react_agent",
    "run_react_agent",
    "AgentState",
]