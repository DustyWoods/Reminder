"""
任务处理工作流 - 精简版（备用）

保留简化的 LangGraph 工作流，用于需要多步骤工具调用的场景
"""
from typing import TypedDict, Annotated, Optional, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from agent.config import get_config
from agent.tools import get_tool_registry
from datetime import datetime, timedelta
from utils import get_logger

logger = get_logger(__name__)


class WorkflowState(TypedDict):
    """工作流状态"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    operation: str
    result: Optional[dict]
    error: Optional[str]
    user_id: Optional[int]


class TaskWorkflow:
    """任务处理工作流 - 精简版"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.config = get_config()
        self.llm = llm or ChatOpenAI(
            model=self.config.effective_model,
            api_key=self.config.effective_api_key,
            base_url=self.config.effective_base_url,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
        self.tools = get_tool_registry().get_all_tools()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建工作流图 - 合并意图识别和任务提取为单节点"""
        workflow = StateGraph(WorkflowState)

        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("execute_tools", ToolNode(self.tools))
        workflow.add_node("summarize", self._summarize_node)

        workflow.set_entry_point("analyze")

        # analyze -> execute_tools (如果有工具调用) 或 -> summarize
        workflow.add_conditional_edges(
            "analyze",
            self._has_tool_calls,
            {"tools": "execute_tools", "summary": "summarize"}
        )

        # execute_tools -> summarize（工具执行完直接总结）
        workflow.add_edge("execute_tools", "summarize")
        workflow.add_edge("summarize", END)

        return workflow.compile()

    def _has_tool_calls(self, state: WorkflowState) -> Literal["tools", "summary"]:
        """判断是否需要工具调用"""
        messages = state.get("messages", [])
        if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
            return "tools"
        return "summary"

    def _analyze_node(self, state: WorkflowState) -> dict:
        """分析节点：意图识别 + 任务提取（单次LLM调用）"""
        user_id = state.get("user_id")
        messages = state.get("messages", [])
        user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break

        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = f"""分析用户输入，判断操作类型并使用工具执行。

操作类型：
- create: 创建新任务 -> 使用 create_task 工具
- update: 修改任务 -> 先用 match_task 再 update_task
- delete: 删除任务 -> 先用 match_task 再 delete_task
- query: 查询任务 -> 使用 get_tasks 工具

当前日期: {today}, 明天: {tomorrow}
用户ID: {user_id or 1}

用户输入: {user_input}"""

        llm_with_tools = self.llm.bind_tools(self.tools)
        response = llm_with_tools.invoke([SystemMessage(content=prompt)])

        return {"messages": [response]}

    def _summarize_node(self, state: WorkflowState) -> dict:
        """总结节点"""
        messages = state.get("messages", [])
        result = {"success": True, "message": "操作完成"}

        # 提取工具执行结果
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, dict):
                result.update(msg.content)
            elif hasattr(msg, "content") and isinstance(msg.content, str):
                try:
                    import json
                    result.update(json.loads(msg.content))
                except Exception:
                    pass

        return {"result": result}

    def invoke(self, text: str, user_id: int = None, **kwargs) -> dict:
        """同步调用"""
        config = kwargs.pop("config", None)
        initial = {
            "messages": [HumanMessage(content=text)],
            "operation": "create",
            "user_id": user_id
        }
        result = self.graph.invoke(initial, config=config)
        return result

    async def ainvoke(self, text: str, user_id: int = None, **kwargs) -> dict:
        """异步调用"""
        config = kwargs.pop("config", None)
        initial = {
            "messages": [HumanMessage(content=text)],
            "operation": "create",
            "user_id": user_id
        }
        result = await self.graph.ainvoke(initial, config=config)
        return result


def create_task_workflow(llm: Optional[ChatOpenAI] = None) -> TaskWorkflow:
    """创建任务工作流实例"""
    return TaskWorkflow(llm=llm)