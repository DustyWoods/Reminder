"""
ReAct Agent 的动作执行函数

包含：
- LLM 驱动的语义匹配
- LLM 驱动的时间解析
- 数据库 CRUD 操作封装
"""
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from .prompts import build_match_prompt
from utils import get_logger, parse_llm_json
from utils.database import (
    create_task, get_tasks_by_user_id, get_task_by_id,
    update_task, delete_task,
)

logger = get_logger(__name__)


# ==================== 规划解析 ====================

def parse_plan_json(content: str) -> list[dict]:
    """解析 LLM 规划输出为步骤列表"""
    data = parse_llm_json(content)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "steps" in data:
        return data["steps"]
    return []


# ==================== LLM 语义匹配 ====================

async def llm_semantic_match(
    llm: ChatOpenAI,
    target_description: str,
    existing_tasks: list[dict],
    operation: str = "update"
) -> dict:
    """
    使用 LLM 进行语义匹配，从任务列表中找出目标任务
    
    Returns:
        {"success": bool, "task_id": int|None, "confidence": str, "message": str}
    """
    if not existing_tasks:
        return {"success": False, "task_id": None, "confidence": "low", "message": "没有可用的任务"}

    # 快速精确匹配
    for t in existing_tasks:
        if t["title"] == target_description:
            return {"success": True, "task_id": t["id"], "confidence": "high", "message": f"精确匹配: {t['title']}"}

    # 单任务直接返回
    if len(existing_tasks) == 1:
        t = existing_tasks[0]
        return {"success": True, "task_id": t["id"], "confidence": "medium", "message": f"唯一任务: {t['title']}"}

    # LLM 语义匹配
    prompt = build_match_prompt(target_description, existing_tasks, operation)
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        result = parse_llm_json(response.content)
        if result and isinstance(result, dict):
            task_id = result.get("task_id")
            if task_id and any(t["id"] == task_id for t in existing_tasks):
                return {
                    "success": True, "task_id": task_id,
                    "confidence": result.get("confidence", "high"),
                    "message": "语义匹配成功"
                }
        return {"success": False, "task_id": None, "confidence": "low", "message": "无法匹配到目标任务"}
    except Exception as e:
        logger.error(f"Semantic match failed: {e}")
        return {"success": False, "task_id": None, "confidence": "low", "message": f"匹配失败: {e}"}


# ==================== LLM 时间解析 ====================

async def llm_parse_time(llm: ChatOpenAI, time_expression: str) -> str:
    """
    使用 LLM 解析自然语言时间表达式
    
    Returns:
        "YYYY-MM-DD HH:MM"
    """
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = f"""将自然语言时间表达式转换为标准格式。

当前时间: {now}
今天: {today}
明天: {tomorrow}

时间表达式: {time_expression}

规则：
- "下午三点" → {today} 15:00
- "明天上午九点" → {tomorrow} 09:00
- "晚上八点" → {today} 20:00
- "半小时后" → 计算当前时间+30分钟
- 无明确时间 → {today} 23:59

输出格式: YYYY-MM-DD HH:MM
只输出时间字符串，不要其他内容。"""

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        time_str = response.content.strip()
        datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        return time_str
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M")


# ==================== 数据库 CRUD ====================

def execute_create(user_id: int, params: dict) -> dict:
    """执行创建操作"""
    title = params.get("title", "新任务")[:10]
    due_date = params.get("due_date", datetime.now().strftime("%Y-%m-%d %H:%M"))
    description = params.get("description", "")

    task_id = create_task(user_id, title, due_date, description)
    task = get_task_by_id(task_id, user_id)
    return {
        "success": True, "task_id": task_id,
        "title": title, "due_date": due_date,
        "description": description, "message": "创建成功",
        "task_data": task
    }


async def execute_update(
    llm: ChatOpenAI, user_id: int, params: dict, existing_tasks: list[dict]
) -> dict:
    """执行更新操作：LLM 匹配目标 + 数据库更新"""
    target_desc = params.get("target_description", "")
    if not target_desc:
        return {"success": False, "message": "缺少目标描述", "task_id": None}

    match = await llm_semantic_match(llm, target_desc, existing_tasks, "update")
    if not match["success"]:
        return {"success": False, "message": match["message"], "task_id": None}

    task_id = match["task_id"]
    update_params = {k: params[k] for k in ("title", "due_date", "description") if params.get(k) is not None}
    if not update_params:
        return {"success": False, "message": "没有提供更新字段", "task_id": task_id}

    if not update_task(task_id, user_id, **update_params):
        return {"success": False, "message": "数据库更新失败", "task_id": task_id}

    updated = get_task_by_id(task_id, user_id)
    return {"success": True, "task_id": task_id, "message": "更新成功", "task_data": updated}


async def execute_delete(
    llm: ChatOpenAI, user_id: int, params: dict, existing_tasks: list[dict]
) -> dict:
    """执行删除操作：LLM 匹配目标 + 数据库删除"""
    target_desc = params.get("target_description", "")
    if not target_desc:
        return {"success": False, "message": "缺少目标描述", "task_id": None}

    match = await llm_semantic_match(llm, target_desc, existing_tasks, "delete")
    if not match["success"]:
        return {"success": False, "message": match["message"], "task_id": None}

    task_id = match["task_id"]
    success = delete_task(task_id, user_id)
    return {
        "success": True if success else False,
        "task_id": task_id,
        "message": "删除成功" if success else "数据库删除失败"
    }


def execute_query(user_id: int) -> dict:
    """执行查询操作"""
    tasks = get_tasks_by_user_id(user_id)
    return {
        "success": True,
        "task_count": len(tasks),
        "tasks": tasks,
        "message": f"共 {len(tasks)} 个任务"
    }