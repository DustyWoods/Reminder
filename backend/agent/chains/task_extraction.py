"""
任务提取链 - 精简版

单次LLM调用完成意图识别 + 任务提取
"""
import json
import re
from typing import Optional, List
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from models import ReminderResponse
from agent.config import get_config
from utils import get_logger

logger = get_logger(__name__)


class TaskExtractionChain:
    """任务提取链 - 精简版：单次LLM调用完成意图识别+任务提取"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.config = get_config()
        self.llm = llm or ChatOpenAI(
            model=self.config.effective_model,
            api_key=self.config.effective_api_key,
            base_url=self.config.effective_base_url,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
        self._extraction_system = self._build_extraction_system_prompt()
        self._operation_system = self._build_operation_system_prompt()

    # ==================== 系统提示词 ====================

    def _build_extraction_system_prompt(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return f"""从自然语言中提取任务。今天是{today}，明天是{tomorrow}。

规则：
- 逐条识别每个独立任务，不要合并或遗漏
- 排除纯背景信息（如"五点才下班"），仅提取有明确动作的任务
- 标题简洁，包含核心动宾结构，不超过{self.config.max_title_length}字
- 时间结合上下文推断上午/下午，"八点"默认晚上，"早上八点"才是上午
- 模糊时间（如下班前）保留在标题中，截止日期用推断的基准时间
- due_date 格式: YYYY-MM-DD HH:MM
- 任务描述需要详细描述任务的具体内容，包括任务的详细信息、要求、注意事项等。

输出纯JSON数组（不要markdown代码块）：
[{{"title": "...", "due_date": "YYYY-MM-DD HH:MM", "description": "..."}}]
如无任何任务，输出空数组：[]"""

    def _build_operation_system_prompt(self) -> str:
        return """分析用户输入，判断操作类型并提取任务信息。

## 操作类型判断
- **create**: 创建新任务（默认）。如"下午三点开会"、"明天交报告"、"提醒我买牛奶"
- **update**: 修改已有任务。如"把会议改到四点"、"推迟遛狗"、"更新任务标题"
- **delete**: 删除任务。如"删除会议"、"取消提醒"、"去掉那个任务"
- **query**: 查询任务。如"今天有什么任务"、"查看任务"、"显示所有任务"

## 输出格式
纯JSON（不要markdown代码块）：
{"operation": "create|update|delete|query", "tasks": [{"title": "...", "due_date": "YYYY-MM-DD HH:MM", "description": "..."}], "task_id": null}

注意：
- operation 默认 create（大多数输入都是创建任务）
- update/delete 时 tasks 可为空（由后端从数据库匹配）
- task_id 仅在用户明确指定ID时填写"""

    # ==================== 同步接口 ====================

    def invoke(self, text: str) -> List[ReminderResponse]:
        """提取任务（不识别操作意图）"""
        return self._do_extract(text)

    def invoke_with_operation(self, text: str) -> dict:
        """意图识别+任务提取"""
        return self._do_operation_extract(text)

    # ==================== 异步接口 ====================

    async def ainvoke(self, text: str) -> List[ReminderResponse]:
        """异步提取任务"""
        return await self._do_extract_async(text)

    async def ainvoke_with_operation(self, text: str) -> dict:
        """异步意图识别+任务提取"""
        return await self._do_operation_extract_async(text)

    # ==================== 核心逻辑 ====================

    def _do_extract(self, text: str) -> List[ReminderResponse]:
        """执行任务提取"""
        try:
            messages = [
                SystemMessage(content=self._extraction_system),
                HumanMessage(content=text)
            ]
            response = self.llm.invoke(messages)
            tasks = self._parse_task_list_json(response.content)
            if tasks:
                logger.info(f"Extracted {len(tasks)} tasks")
                return tasks
            return self._build_fallback_tasks(text)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return self._build_fallback_tasks(text)

    async def _do_extract_async(self, text: str) -> List[ReminderResponse]:
        """异步执行任务提取"""
        try:
            messages = [
                SystemMessage(content=self._extraction_system),
                HumanMessage(content=text)
            ]
            response = await self.llm.ainvoke(messages)
            tasks = self._parse_task_list_json(response.content)
            if tasks:
                logger.info(f"Extracted {len(tasks)} tasks")
                return tasks
            return self._build_fallback_tasks(text)
        except Exception as e:
            logger.error(f"Async extraction failed: {e}")
            return self._build_fallback_tasks(text)

    def _do_operation_extract(self, text: str) -> dict:
        """执行意图识别+任务提取"""
        try:
            messages = [
                SystemMessage(content=self._operation_system),
                HumanMessage(content=text)
            ]
            response = self.llm.invoke(messages)
            return self._parse_operation_result(response.content, text)
        except Exception as e:
            logger.error(f"Operation extraction failed: {e}")
            return {"operation": "create", "tasks": self._build_fallback_tasks(text), "task_id": None}

    async def _do_operation_extract_async(self, text: str) -> dict:
        """异步执行意图识别+任务提取"""
        try:
            messages = [
                SystemMessage(content=self._operation_system),
                HumanMessage(content=text)
            ]
            response = await self.llm.ainvoke(messages)
            return self._parse_operation_result(response.content, text)
        except Exception as e:
            logger.error(f"Async operation extraction failed: {e}")
            return {"operation": "create", "tasks": self._build_fallback_tasks(text), "task_id": None}

    # ==================== JSON 解析（统一） ====================

    @staticmethod
    def _extract_json(content: str) -> Optional[dict | list]:
        """从LLM响应中提取JSON，处理markdown代码块等干扰"""
        content = content.strip()
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 {...} 或 [...]
            for pattern in [r'\[.*\]', r'\{.*\}']:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group())
                    except json.JSONDecodeError:
                        continue
            return None

    def _parse_task_list_json(self, content: str) -> List[ReminderResponse]:
        """解析任务列表JSON（支持数组和对象两种格式）"""
        data = self._extract_json(content)
        if data is None:
            return []

        if isinstance(data, list):
            return [ReminderResponse(**t) for t in data if isinstance(t, dict)]
        if isinstance(data, dict):
            items = data.get("tasks", [])
            return [ReminderResponse(**t) for t in items if isinstance(t, dict)]
        return []

    def _parse_operation_result(self, content: str, text: str = "") -> dict:
        """解析操作意图识别结果"""
        parsed = self._extract_json(content)
        if parsed is None or not isinstance(parsed, dict):
            logger.warning("JSON parse failed, defaulting to create")
            return {"operation": "create", "tasks": self._build_fallback_tasks(text), "task_id": None}

        operation = parsed.get("operation", "create")
        if operation not in ("create", "update", "delete", "query"):
            operation = "create"

        tasks = []
        tasks_data = parsed.get("tasks", [])
        if isinstance(tasks_data, list):
            for t in tasks_data:
                if isinstance(t, dict):
                    try:
                        tasks.append(ReminderResponse(**t))
                    except Exception:
                        pass

        return {"operation": operation, "tasks": tasks, "task_id": parsed.get("task_id")}

    # ==================== 降级处理 ====================

    def _build_fallback_tasks(self, text: str) -> List[ReminderResponse]:
        """降级：将原始文本作为单个任务"""
        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        return [ReminderResponse(
            title=title,
            due_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            description=text
        )]