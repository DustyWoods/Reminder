"""
ReAct Agent 图节点

节点：
- plan_node: LLM 分析用户输入，拆解为操作步骤
- act_node: 执行当前步骤
- observe_node: 验证执行结果，决定重试/继续
- summarize_node: 生成用户友好的总结
"""
from datetime import datetime, timedelta
from typing import Literal

from langchain_core.messages import HumanMessage

from .state import AgentState, StepResult
from .prompts import build_plan_prompt, build_summarize_prompt
from .actions import (
    parse_plan_json, execute_create, execute_update, execute_delete, execute_query,
)
from utils import get_logger, build_llm
from utils.database import get_tasks_by_user_id

logger = get_logger(__name__)


def _filter_recent_tasks(tasks: list[dict], days: int = 7) -> list[dict]:
    """过滤近 N 天内的任务，减少 LLM 上下文长度"""
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for t in tasks:
        due_str = t.get("due_date")
        if due_str:
            try:
                due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
                if due_dt >= cutoff:
                    recent.append(t)
                # due_date 太旧的任务跳过
                continue
            except ValueError:
                pass
        # 没有 due_date 或格式异常的任务也保留
        recent.append(t)
    return recent


# ==================== Plan Node ====================

async def plan_node(state: AgentState) -> dict:
    """
    规划节点：LLM 分析输入，生成操作步骤列表
    
    步骤格式: [{step, operation, description, params}, ...]
    """
    user_input = state["user_input"]
    user_id = state["user_id"]
    logger.info(f"[Plan] Analyzing: '{user_input[:80]}' for user {user_id}")

    all_tasks = get_tasks_by_user_id(user_id)
    existing_tasks = _filter_recent_tasks(all_tasks)
    logger.info(f"[Plan] Context tasks: {len(existing_tasks)}/{len(all_tasks)} (filtered to last 7 days)")
    llm = build_llm()
    prompt = build_plan_prompt(user_input, existing_tasks)

    fallback_plan = [{
        "step": 1, "operation": "create", "description": user_input,
        "params": {
            "title": user_input[:10],
            "due_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "description": user_input
        }
    }]

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        plan = parse_plan_json(response.content) or fallback_plan
        logger.info(f"[Plan] Generated {len(plan)} steps: {[s['operation'] for s in plan]}")
        return {
            "plan": plan, "plan_raw": response.content,
            "current_step": 0, "results": [],
            "needs_retry": False, "retry_count": 0, "max_retries": 2,
            "error": None, "finished": False
        }
    except Exception as e:
        logger.error(f"[Plan] Failed: {e}")
        return {
            "plan": fallback_plan, "plan_raw": "",
            "current_step": 0, "results": [],
            "needs_retry": False, "retry_count": 0, "max_retries": 2,
            "error": None, "finished": False
        }


# ==================== Act Node ====================

async def act_node(state: AgentState) -> dict:
    """执行节点：执行当前步骤的操作"""
    step_idx = state["current_step"]
    plan = state["plan"]
    user_id = state["user_id"]

    if step_idx >= len(plan):
        return {}

    step = plan[step_idx]
    operation = step.get("operation", "create")
    params = step.get("params", {})
    logger.info(f"[Act] Step {step_idx+1}/{len(plan)}: {operation} - {step.get('description', '')}")

    llm = build_llm()
    existing_tasks = get_tasks_by_user_id(user_id)

    try:
        if operation == "create":
            result = execute_create(user_id, params)
        elif operation == "update":
            result = await execute_update(llm, user_id, params, existing_tasks)
        elif operation == "delete":
            result = await execute_delete(llm, user_id, params, existing_tasks)
        elif operation == "query":
            result = execute_query(user_id)
        else:
            result = {"success": False, "message": f"未知操作类型: {operation}"}

        logger.info(f"[Act] success={result.get('success')}, msg={result.get('message')}")

        step_result: StepResult = {
            "step_index": step_idx,
            "operation": operation,
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "task_id": result.get("task_id"),
            "task_title": result.get("title"),
            "task_data": result.get("task_data"),
        }
        new_results = list(state.get("results", []))
        new_results.append(step_result)

        return {
            "results": new_results,
            "needs_retry": not step_result["success"] and state.get("retry_count", 0) < state.get("max_retries", 2),
            "retry_count": 0,
            "error": None if step_result["success"] else step_result["message"]
        }
    except Exception as e:
        logger.error(f"[Act] Failed: {e}")
        step_result: StepResult = {
            "step_index": step_idx, "operation": operation,
            "success": False, "message": str(e),
            "task_id": None, "task_title": None, "task_data": None,
        }
        new_results = list(state.get("results", []))
        new_results.append(step_result)
        return {
            "results": new_results,
            "needs_retry": state.get("retry_count", 0) < state.get("max_retries", 2),
            "retry_count": state.get("retry_count", 0) + 1,
            "error": str(e)
        }


# ==================== Observe Node ====================

async def observe_node(state: AgentState) -> dict:
    """观察节点：验证结果，决定重试或继续"""
    results = state.get("results", [])
    if not results:
        return {}

    last = results[-1]
    logger.info(f"[Observe] Step {last['step_index']+1}: success={last['success']}")

    if last["success"]:
        return {"needs_retry": False, "retry_count": 0, "error": None}

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    if retry_count < max_retries:
        logger.info(f"[Observe] Retry step {last['step_index']+1} ({retry_count+1}/{max_retries})")
        return {"needs_retry": True, "retry_count": retry_count + 1}
    else:
        logger.warning(f"[Observe] Max retries reached for step {last['step_index']+1}")
        return {"needs_retry": False, "error": f"步骤 {last['step_index']+1} 失败: {last['message']}"}


# ==================== Summarize Node ====================

async def summarize_node(state: AgentState) -> dict:
    """总结节点：生成用户友好的操作总结"""
    results = state.get("results", [])
    logger.info(f"[Summarize] Generating summary for {len(results)} results")

    if not results:
        return {"summary": "未能处理您的请求，请重试。", "finished": True}

    # 全部成功 → 快速拼接
    if all(r["success"] for r in results):
        return _quick_summary(results)

    # 有失败 → LLM 总结
    llm = build_llm()
    results_dict = [dict(r) for r in results]
    prompt = build_summarize_prompt(state["user_input"], results_dict)
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return {"summary": response.content.strip(), "finished": True}
    except Exception:
        success_count = sum(1 for r in results if r["success"])
        return {"summary": f"共 {len(results)} 项操作，{success_count} 项成功。", "finished": True}


def _quick_summary(results: list) -> dict:
    """快速拼接成功总结（不调用 LLM）"""
    ops = []
    for r in results:
        if r["operation"] == "create":
            ops.append(f"创建了「{r.get('task_title', '任务')}」")
        elif r["operation"] == "update":
            ops.append("更新了任务")
        elif r["operation"] == "delete":
            ops.append("删除了任务")
        elif r["operation"] == "query":
            return {"summary": f"查询完成，{r.get('message', '')}", "finished": True}
    return {"summary": "、".join(ops) + "。", "finished": True}


# ==================== 路由函数 ====================

def route_after_plan(state: AgentState) -> Literal["act", "summarize"]:
    """规划完成 → 执行或总结"""
    return "summarize" if not state.get("plan") else "act"


def route_after_observe(state: AgentState) -> Literal["act", "summarize"]:
    """观察完成 → 递增步骤继续 / 总结"""
    if state.get("needs_retry", False):
        return "act"
    next_step = state.get("current_step", 0) + 1
    return "act" if next_step < len(state.get("plan", [])) else "summarize"


def route_after_act(state: AgentState) -> Literal["observe", "summarize"]:
    """执行完成 → 观察或直接总结"""
    step_idx = state.get("current_step", 0)
    plan = state.get("plan", [])
    results = state.get("results", [])
    last_ok = results[-1]["success"] if results else False
    return "summarize" if step_idx + 1 >= len(plan) and last_ok else "observe"


def step_increment(state: AgentState) -> dict:
    """递增当前步骤索引"""
    return {"current_step": state.get("current_step", 0) + 1}