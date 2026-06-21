"""
Agent 状态定义 - 贯穿整个 ReAct 流程的状态
"""
from typing import TypedDict, Optional


class StepResult(TypedDict):
    """单个操作步骤的结果"""
    step_index: int
    operation: str          # create / update / delete / query
    success: bool
    message: str
    task_id: Optional[int]
    task_title: Optional[str]
    task_data: Optional[dict]


class AgentState(TypedDict):
    """ReAct Agent 全局状态"""
    # 输入
    user_input: str
    user_id: int

    # 规划阶段
    plan: list[dict]        # LLM 规划的步骤列表: [{op, params, description}, ...]
    plan_raw: str           # LLM 原始规划输出

    # 执行阶段
    current_step: int       # 当前执行到的步骤索引
    results: list[StepResult]  # 各步骤执行结果

    # 循环控制
    needs_retry: bool       # 当前步骤是否需要重试
    retry_count: int        # 当前步骤重试次数
    max_retries: int        # 最大重试次数

    # 最终输出
    summary: str            # 给用户的总结
    finished: bool
    error: Optional[str]    # 全局错误