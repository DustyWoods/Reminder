"""
任务助手智能体 - 精简版

核心流程（单次LLM调用）：
1. LLM判断用户需求类型（create/update/delete/query）
2. 根据类型规划处理顺序并提取参数
3. 后端执行数据库操作
4. 返回统一格式结果
"""
from typing import Optional, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from models import ReminderResponse
from agent.config import AgentConfig
from agent.agents.base import BaseAgent
from agent.chains import TaskExtractionChain, FallbackChain
from agent.tools import get_tool_registry
from utils import get_logger
from utils.database import (
    get_tasks_by_user_id, get_task_by_id,
    update_task, delete_task, create_task,
)

logger = get_logger(__name__)


class TaskAgent(BaseAgent):
    """任务助手智能体 - 精简版"""

    def __init__(
        self,
        name: str = "task_agent",
        version: str = "3.0.0",
        llm: Optional[ChatOpenAI] = None,
        config: Optional[AgentConfig] = None
    ):
        super().__init__(name=name, version=version, llm=llm, config=config)

        self.tool_registry = get_tool_registry()
        self.tools = self.tool_registry.get_all_tools()
        self.extraction_chain = TaskExtractionChain(llm=self.llm)
        self.fallback_chain = FallbackChain()
        self._initialized = True
        logger.info(f"TaskAgent '{name}' v{version} initialized")

    # ==================== 主入口 ====================

    async def process(self, text: str, user_id: int = 1) -> dict:
        """
        统一处理入口：意图识别 + 任务处理

        流程：
        1. LLM判断操作类型并提取参数
        2. update/delete 时先从数据库获取任务列表供LLM匹配
        3. 执行数据库操作
        4. 返回统一格式结果

        Returns:
            {"operation": str, "success": bool, "message": str, "tasks": list}
        """
        logger.info(f"Processing: '{text[:80]}', user_id={user_id}")

        if not self.is_available():
            return self._fallback_result(text, user_id)

        try:
            # 1. LLM 意图识别 + 任务提取（单次调用）
            llm_result = await self.extraction_chain.ainvoke_with_operation(text)

            operation = llm_result.get("operation", "create")
            tasks = llm_result.get("tasks", [])
            task_id = llm_result.get("task_id")

            logger.info(f"LLM detected operation={operation}, tasks={len(tasks)}, task_id={task_id}")

            # 2. 根据操作类型执行
            if operation == "create":
                return self._do_create(tasks, user_id)
            elif operation == "update":
                return await self._do_update(text, user_id, tasks, task_id)
            elif operation == "delete":
                return await self._do_delete(text, user_id, tasks, task_id)
            elif operation == "query":
                return self._do_query(user_id)
            else:
                return self._do_create(tasks, user_id)

        except Exception as e:
            logger.error(f"Process failed: {e}")
            return self._fallback_result(text, user_id)

    def invoke(self, text: str, **kwargs) -> List[ReminderResponse]:
        """同步任务提取（仅提取，不操作数据库）"""
        try:
            return self.extraction_chain.invoke(text)
        except Exception as e:
            logger.error(f"Invoke failed: {e}")
            return self.fallback_chain.invoke(text)

    async def ainvoke(self, text: str, **kwargs) -> List[ReminderResponse]:
        """异步任务提取（仅提取，不操作数据库）"""
        try:
            return await self.extraction_chain.ainvoke(text)
        except Exception as e:
            logger.error(f"Async invoke failed: {e}")
            return self.fallback_chain.invoke(text)

    # ==================== 操作执行 ====================

    def _do_create(self, tasks: List[ReminderResponse], user_id: int) -> dict:
        """执行创建操作"""
        if not tasks:
            return {"operation": "create", "success": False, "message": "未识别到任务信息", "tasks": []}

        saved = []
        for t in tasks:
            tid = create_task(user_id, t.title, t.due_date, t.description)
            saved.append({
                "id": tid, "title": t.title, "due_date": t.due_date,
                "description": t.description, "completed": False
            })

        logger.info(f"Created {len(saved)} tasks for user {user_id}")
        return {"operation": "create", "success": True, "message": f"成功创建 {len(saved)} 个任务", "tasks": saved}

    async def _do_update(self, text: str, user_id: int, tasks: List[ReminderResponse], task_id: int = None) -> dict:
        """执行更新操作 —— 从数据库获取任务列表，让LLM匹配要更新的任务"""
        db_tasks = get_tasks_by_user_id(user_id)
        if not db_tasks:
            return {"operation": "update", "success": False, "message": "没有可更新的任务", "tasks": []}

        # 让LLM从任务列表中匹配目标并提取更新参数
        match_result = await self._llm_match_and_extract(text, db_tasks, "update")
        if not match_result.get("success"):
            return {"operation": "update", "success": False, "message": match_result.get("message", "无法匹配任务"), "tasks": []}

        task_id = match_result["task_id"]
        update_params = match_result.get("update_params", {})

        if not update_params:
            return {"operation": "update", "success": False, "message": "没有提供更新字段", "tasks": []}

        success = update_task(task_id, user_id, **update_params)
        if not success:
            return {"operation": "update", "success": False, "message": "更新失败，任务不存在或无权限", "tasks": []}

        updated = get_task_by_id(task_id, user_id)
        if updated and "user_id" not in updated:
            updated["user_id"] = user_id
        return {"operation": "update", "success": True, "message": "任务更新成功", "tasks": [updated] if updated else []}

    async def _do_delete(self, text: str, user_id: int, tasks: List[ReminderResponse], task_id: int = None) -> dict:
        """执行删除操作 —— 从数据库获取任务列表，让LLM匹配要删除的任务"""
        db_tasks = get_tasks_by_user_id(user_id)
        if not db_tasks:
            return {"operation": "delete", "success": False, "message": "没有可删除的任务", "tasks": []}

        # 用户明确指定了task_id
        if task_id:
            success = delete_task(task_id, user_id)
            if success:
                return {"operation": "delete", "success": True, "message": "任务删除成功", "tasks": [{"id": task_id}]}
            return {"operation": "delete", "success": False, "message": "删除失败", "tasks": []}

        # 让LLM从任务列表中匹配要删除的目标
        match_result = await self._llm_match_and_extract(text, db_tasks, "delete")
        if not match_result.get("success"):
            return {"operation": "delete", "success": False, "message": match_result.get("message", "无法匹配任务"), "tasks": []}

        task_id = match_result["task_id"]
        success = delete_task(task_id, user_id)
        if success:
            return {"operation": "delete", "success": True, "message": "任务删除成功", "tasks": [{"id": task_id}]}
        return {"operation": "delete", "success": False, "message": "删除失败", "tasks": []}

    def _do_query(self, user_id: int) -> dict:
        """执行查询操作"""
        tasks = get_tasks_by_user_id(user_id)
        return {"operation": "query", "success": True, "message": f"共 {len(tasks)} 个任务", "tasks": tasks}

    # ==================== LLM 辅助 ====================

    async def _llm_match_and_extract(self, user_input: str, db_tasks: list, operation: str) -> dict:
        """
        LLM从任务列表中匹配目标，并提取操作参数

        对于 update: 返回匹配的 task_id + 更新字段
        对于 delete: 返回匹配的 task_id
        """
        import json, re
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        tasks_desc = "\n".join([
            f"  ID={t['id']} | 标题={t['title']} | 时间={t['due_date']} | 描述={t.get('description','')}"
            for t in db_tasks
        ])

        prompt = f"""从任务列表中匹配用户要{operation == 'update' and '修改' or '删除'}的任务。

## 当前时间
今天是 {today}，明天是 {tomorrow}。

## 用户输入
{user_input}

## 任务列表
{tasks_desc}"""

        if operation == "update":
            prompt += """

## 输出格式
{"task_id": 数字, "update_params": {"title": "新标题(可选)", "due_date": "YYYY-MM-DD HH:MM(可选)", "description": "新描述(可选)"}}

## 注意
- 只输出需要修改的字段，不改的字段不要出现
- 时间变化需计算具体值（如"改到明天下午三点"→明天15:00的日期）
- 无法确定任务时 task_id 设为 null"""
        else:
            prompt += """

## 输出格式
{"task_id": 数字或null}

## 注意
- 用户输入明确指向某个任务时返回其ID
- 无法确定时 task_id 设为 null"""

        prompt += "\n只输出JSON，不要其他内容。"

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content

            # 提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)

            task_id = result.get("task_id")
            if not task_id:
                return {"success": False, "message": "无法确定目标任务"}

            # 验证 task_id
            valid_ids = {t["id"] for t in db_tasks}
            if task_id not in valid_ids:
                return {"success": False, "message": "匹配的任务ID不存在"}

            out = {"success": True, "task_id": task_id}
            if operation == "update":
                out["update_params"] = result.get("update_params", {})
            return out

        except Exception as e:
            logger.error(f"LLM matching failed: {e}")
            return {"success": False, "message": "任务匹配失败"}

    # ==================== 降级 ====================

    def _fallback_result(self, text: str, user_id: int) -> dict:
        """降级处理：使用 FallbackChain 创建简单任务"""
        fallback_tasks = self.fallback_chain.invoke(text)
        return self._do_create(fallback_tasks, user_id)

    # ==================== 公共方法（兼容旧接口） ====================

    def execute_query(self, user_id: int) -> dict:
        return self._do_query(user_id)

    def execute_delete(self, user_id: int, task_id: int = None, task_title: str = None) -> dict:
        """同步删除（兼容旧接口）"""
        if task_id:
            success = delete_task(task_id, user_id)
            return {
                "operation": "delete", "success": success,
                "message": "删除成功" if success else "删除失败",
                "tasks": [{"id": task_id}] if success else []
            }
        return {"operation": "delete", "success": False, "message": "请提供任务ID", "tasks": []}

    def execute_update(self, tasks: List[ReminderResponse], user_id: int, task_id: int = None) -> dict:
        """同步更新（兼容旧接口）"""
        if not task_id or not tasks:
            return {"operation": "update", "success": False, "message": "参数不足", "tasks": []}
        t = tasks[0]
        params = {}
        if t.title: params["title"] = t.title
        if t.due_date: params["due_date"] = t.due_date
        if t.description: params["description"] = t.description
        if not params:
            return {"operation": "update", "success": False, "message": "无更新字段", "tasks": []}
        success = update_task(task_id, user_id, **params)
        updated = get_task_by_id(task_id, user_id) if success else None
        return {
            "operation": "update", "success": success,
            "message": "更新成功" if success else "更新失败",
            "tasks": [updated] if updated else []
        }


# 全局实例
task_agent = TaskAgent()


def get_task_agent() -> TaskAgent:
    return task_agent