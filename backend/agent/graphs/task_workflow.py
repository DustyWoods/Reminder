"""
任务处理工作流
"""
from typing import TypedDict, Annotated, Literal, Optional, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from agent.config import get_config
from agent.tools import get_tool_registry
from utils import get_logger

logger = get_logger(__name__)


class WorkflowState(TypedDict):
    """
    工作流状态
    
    使用 TypedDict 定义 LangGraph 的状态结构
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    task_extracted: bool
    result: Optional[dict]
    error: Optional[str]


class TaskWorkflow:
    """
    任务处理工作流
    
    使用 LangGraph 构建的状态图，包含以下节点：
    1. analyze: 分析用户输入
    2. extract: 提取任务信息
    3. validate: 验证提取结果
    4. fallback: 备用处理
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        初始化任务工作流
        
        Args:
            llm: LLM 实例（可选）
        """
        self.config = get_config()
        self.llm = llm or self._create_llm()
        self.tools = self._load_tools()
        self.graph = self._build_graph()
    
    def _create_llm(self) -> ChatOpenAI:
        """创建 LLM 实例"""
        return ChatOpenAI(
            model=self.config.effective_model,
            api_key=self.config.effective_api_key,
            base_url=self.config.effective_base_url,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
    
    def _load_tools(self) -> list[BaseTool]:
        """加载工具"""
        registry = get_tool_registry()
        tools = registry.get_all_tools()
        logger.info(f"Loaded {len(tools)} tools for workflow")
        return tools
    
    def _build_graph(self) -> StateGraph:
        """
        构建工作流图
        
        Returns:
            StateGraph: 编译后的状态图
        """
        # 创建状态图
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("analyze", self.analyze_node)
        workflow.add_node("extract", self.extract_node)
        workflow.add_node("validate", self.validate_node)
        workflow.add_node("fallback", self.fallback_node)
        
        # 添加工具节点
        tool_node = ToolNode(self.tools)
        workflow.add_node("tools", tool_node)
        
        # 设置入口点
        workflow.set_entry_point("analyze")
        
        # 添加边
        workflow.add_edge("analyze", "extract")
        workflow.add_edge("extract", "validate")
        
        # 条件边：根据验证结果决定下一步
        workflow.add_conditional_edges(
            "validate",
            self.should_continue,
            {
                "continue": "tools",
                "end": END,
                "fallback": "fallback"
            }
        )
        
        # 工具执行后返回验证
        workflow.add_edge("tools", "validate")
        
        # 备用处理后结束
        workflow.add_edge("fallback", END)
        
        # 编译图
        checkpointer = MemorySaver() if self.config.graph_checkpointer else None
        compiled_graph = workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=None
        )
        
        logger.info("Task workflow compiled successfully")
        return compiled_graph
    
    def analyze_node(self, state: WorkflowState) -> dict:
        """
        分析节点：分析用户输入
        
        Args:
            state: 当前工作流状态
            
        Returns:
            dict: 状态更新
        """
        logger.info("Analyzing user input")
        
        messages = state["messages"]
        if not messages:
            return {
                "error": "No input messages",
                "task_extracted": False
            }
        
        last_message = messages[-1]
        logger.info(f"Analyzing message: {last_message.content[:50]}...")
        
        return {
            "task_extracted": False,
            "result": None
        }
    
    def extract_node(self, state: WorkflowState) -> dict:
        """
        提取节点：使用 LLM 提取任务信息
        
        Args:
            state: 当前工作流状态
            
        Returns:
            dict: 状态更新
        """
        logger.info("Extracting task information")
        
        messages = state["messages"]
        
        # 构建系统提示
        system_prompt = f"""
你是一个智能任务助手。请分析用户输入并提取任务信息。
使用提供的工具来创建结构化的任务。

要求：
- 标题不超过{self.config.max_title_length}个字符
- 日期格式为 YYYY-MM-DD HH:MM
- 包含所有相关细节
"""
        
        # 添加系统消息
        all_messages = [AIMessage(content=system_prompt)] + list(messages)
        
        # 调用 LLM（带工具）
        response = self.llm.bind_tools(self.tools).invoke(all_messages)
        
        return {
            "messages": [response]
        }
    
    def validate_node(self, state: WorkflowState) -> dict:
        """
        验证节点：验证提取结果
        
        Args:
            state: 当前工作流状态
            
        Returns:
            dict: 状态更新
        """
        logger.info("Validating extracted information")
        
        messages = state["messages"]
        last_message = messages[-1]
        
        # 检查是否有工具调用
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info("Tool calls detected")
            return {}
        
        # 检查是否有有效内容
        if hasattr(last_message, "content") and last_message.content:
            logger.info("Valid content found")
            return {
                "task_extracted": True,
                "result": {"content": last_message.content}
            }
        
        logger.warning("No valid content found")
        return {
            "task_extracted": False,
            "error": "No valid content"
        }
    
    def fallback_node(self, state: WorkflowState) -> dict:
        """
        备用节点：当主要流程失败时使用
        
        Args:
            state: 当前工作流状态
            
        Returns:
            dict: 状态更新
        """
        logger.warning("Using fallback processing")
        
        messages = state["messages"]
        last_user_message = None
        
        # 查找最后一个用户消息
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_message = msg
                break
        
        if not last_user_message:
            return {
                "error": "No user input found",
                "result": None
            }
        
        # 创建简单的备用响应
        text = last_user_message.content[:50] if len(last_user_message.content) > 50 else last_user_message.content
        
        return {
            "task_extracted": True,
            "result": {
                "title": text,
                "due_date": "2026-06-01 12:00",
                "description": last_user_message.content
            }
        }
    
    def should_continue(self, state: WorkflowState) -> Literal["continue", "end", "fallback"]:
        """
        条件判断：决定下一步
        
        Args:
            state: 当前工作流状态
            
        Returns:
            str: 下一个节点
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # 检查是否有工具调用
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        
        # 检查是否成功提取
        if state.get("task_extracted"):
            return "end"
        
        # 检查是否有错误
        if state.get("error"):
            return "fallback"
        
        return "fallback"
    
    def invoke(self, text: str, config: Optional[dict] = None) -> dict:
        """
        执行工作流
        
        Args:
            text: 用户输入的文本
            config: 可选的配置
            
        Returns:
            dict: 工作流结果
        """
        logger.info(f"Invoking workflow with: {text[:50]}...")
        
        initial_state = {
            "messages": [HumanMessage(content=text)],
            "task_extracted": False,
            "result": None,
            "error": None
        }
        
        result = self.graph.invoke(initial_state, config=config)
        
        logger.info(f"Workflow completed, task_extracted: {result.get('task_extracted')}")
        return result
    
    async def ainvoke(self, text: str, config: Optional[dict] = None) -> dict:
        """
        异步执行工作流
        
        Args:
            text: 用户输入的文本
            config: 可选的配置
            
        Returns:
            dict: 工作流结果
        """
        logger.info(f"Async invoking workflow with: {text[:50]}...")
        
        initial_state = {
            "messages": [HumanMessage(content=text)],
            "task_extracted": False,
            "result": None,
            "error": None
        }
        
        result = await self.graph.ainvoke(initial_state, config=config)
        
        logger.info(f"Async workflow completed, task_extracted: {result.get('task_extracted')}")
        return result


def create_task_workflow(llm: Optional[ChatOpenAI] = None) -> TaskWorkflow:
    """
    工厂函数：创建任务工作流
    
    Args:
        llm: LLM 实例（可选）
        
    Returns:
        TaskWorkflow: 任务工作流实例
    """
    return TaskWorkflow(llm=llm)
