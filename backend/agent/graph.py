"""
ReAct Agent 的 LangGraph 图定义

图结构：
    START → plan → [router] → act → observe → [router] → summarize → END
                    ↑                        │
                    └────────────────────────┘ (多步骤循环)
"""
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    plan_node, act_node, observe_node, summarize_node,
    route_after_plan, route_after_observe, route_after_act,
    step_increment,
)


def create_react_agent() -> StateGraph:
    """
    创建 ReAct Agent 图
    
    流程：
    1. plan: LLM 分析用户输入，生成操作步骤
    2. route: 判断是否有步骤需要执行
    3. act: 执行当前步骤（create/update/delete/query）
    4. observe: 验证执行结果，决定重试或继续
    5. 循环 act→observe 直到所有步骤完成
    6. summarize: LLM 生成用户友好的总结
    """
    workflow = StateGraph(AgentState)

    # 注册节点
    workflow.add_node("plan", plan_node)
    workflow.add_node("act", act_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("step_increment", step_increment)

    # 设置入口
    workflow.set_entry_point("plan")

    # 规划后的路由
    workflow.add_conditional_edges(
        "plan",
        route_after_plan,
        {"act": "act", "summarize": "summarize"}
    )

    # 执行后 → 观察/总结
    workflow.add_conditional_edges(
        "act",
        route_after_act,
        {"observe": "observe", "summarize": "summarize"}
    )

    # 观察后 → 递增步骤并继续 / 总结
    workflow.add_conditional_edges(
        "observe",
        route_after_observe,
        {"act": "step_increment", "summarize": "summarize"}
    )

    # 步骤递增后 → 执行
    workflow.add_edge("step_increment", "act")

    # 总结后 → 结束
    workflow.add_edge("summarize", END)

    return workflow.compile()


# 全局编译好的图实例（惰性初始化）
_agent_graph = None


def get_agent_graph():
    """获取全局 Agent 图实例"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_react_agent()
    return _agent_graph


async def run_react_agent(user_input: str, user_id: int) -> dict:
    """
    运行 ReAct Agent
    
    Args:
        user_input: 用户自然语言输入
        user_id: 用户 ID
    
    Returns:
        {
            "success": bool,
            "summary": str,
            "operation": str,
            "tasks": list[dict],
            "results": list[dict],
            "plan": list[dict]
        }
    """
    from utils import get_logger
    logger = get_logger(__name__)

    graph = get_agent_graph()
    initial_state: AgentState = {
        "user_input": user_input,
        "user_id": user_id,
        "plan": [],
        "plan_raw": "",
        "current_step": 0,
        "results": [],
        "needs_retry": False,
        "retry_count": 0,
        "max_retries": 2,
        "summary": "",
        "finished": False,
        "error": None,
    }

    logger.info(f"[ReAct Agent] Starting with input: '{user_input[:80]}'")

    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"[ReAct Agent] Graph execution failed: {e}")
        return {
            "success": False,
            "summary": f"处理失败: {str(e)}",
            "operation": "error",
            "tasks": [],
            "results": [],
            "plan": []
        }

    results = final_state.get("results", [])
    plan = final_state.get("plan", [])

    # 收集所有操作的任务数据
    all_tasks = []
    for r in results:
        if r.get("task_data"):
            all_tasks.append(r["task_data"])
        elif r["operation"] == "create" and r.get("task_id"):
            from utils.database import get_task_by_id
            task = get_task_by_id(r["task_id"], user_id)
            if task:
                all_tasks.append(task)
            else:
                all_tasks.append({
                    "id": r["task_id"],
                    "title": r.get("task_title", ""),
                    "message": r.get("message", "")
                })
        elif r["operation"] == "delete" and r.get("task_id"):
            all_tasks.append({"id": r["task_id"], "deleted": True})

    # 如果是纯查询操作，返回查询到的任务
    if results and results[-1]["operation"] == "query":
        from utils.database import get_tasks_by_user_id
        all_tasks = get_tasks_by_user_id(user_id)

    all_success = all(r["success"] for r in results) if results else False
    operations = list(set(r["operation"] for r in results)) if results else ["unknown"]

    summary = final_state.get("summary", "")
    if not summary and results:
        success_count = sum(1 for r in results if r["success"])
        summary = f"共 {len(results)} 项操作，{success_count} 项成功。"

    logger.info(f"[ReAct Agent] Complete: {len(results)} steps, all_success={all_success}")

    return {
        "success": all_success,
        "summary": summary,
        "operation": operations[0] if len(operations) == 1 else "mixed",
        "operations": operations,
        "tasks": all_tasks,
        "results": [dict(r) for r in results],
        "plan": plan
    }