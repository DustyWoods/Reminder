"""
任务处理工作流 - 优化版

核心优化：
1. 简化工作流结构，减少不必要的节点
2. 让LLM直接处理任务提取，减少中间环节
3. 优化提示词，增强任务拆分和时间分析能力
"""
from typing import TypedDict, Annotated, Literal, Optional, Sequence, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from agent.config import get_config
from agent.tools import get_tool_registry
from datetime import datetime
from models import ReminderResponse
from utils import get_logger

logger = get_logger(__name__)


class WorkflowState(TypedDict):
    """
    工作流状态
    
    使用TypedDict定义LangGraph的状态结构
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    task_extracted: bool
    result: Optional[dict]
    error: Optional[str]


class TaskWorkflow:
    """
    任务处理工作流
    
    使用LangGraph构建的状态图，包含以下节点：
    1. extract: 使用LLM直接提取任务信息
    2. validate: 验证提取结果
    3. tools: 工具执行节点
    4. fallback: 备用处理
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        初始化任务工作流
        
        Args:
            llm: LLM实例（可选）
        """
        self.config = get_config()
        self.llm = llm or self._create_llm()
        self.tools = self._load_tools()
        self.graph = self._build_graph()
    
    def _create_llm(self) -> ChatOpenAI:
        """创建LLM实例"""
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
        
        # 添加节点 - 简化为核心节点
        workflow.add_node("extract", self.extract_node)
        workflow.add_node("validate", self.validate_node)
        workflow.add_node("fallback", self.fallback_node)
        
        # 添加工具节点
        tool_node = ToolNode(self.tools)
        workflow.add_node("tools", tool_node)
        
        # 设置入口点
        workflow.set_entry_point("extract")
        
        # 添加边
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
    
    def extract_node(self, state: WorkflowState) -> dict:
        """
        提取节点：使用LLM直接提取任务信息
        
        Args:
            state: 当前工作流状态
            
        Returns:
            dict: 状态更新
        """
        logger.info("Extracting task information using LLM")
        
        messages = state["messages"]
        
        # 获取当前日期用于提示词中的示例
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 优化后的系统提示词 - 让LLM直接处理任务提取
        system_prompt = f"""
你是一个专业的智能任务提取助手，精通从自然语言文本中准确识别和提取任务信息。

## 核心指令

### 一、任务识别规则
1. **逐条识别**：仔细分析文本，找出每一个独立的任务/事项/提醒
2. **数量准确**：严格按照文本中的任务数量输出，不要合并也不要遗漏
3. **排除背景信息**：陈述性的背景信息（如"五点才下班"、"今天天气不错"）不是任务，仅作为时间参考
4. **任务特征**：任务必须包含明确的动作（动词）和对象（宾语），缺少任何一个都不是有效任务

### 二、时间分析规则
1. **上下文推断**：分析时间时必须结合上下文语境判断是上午还是下午
2. **模糊时间处理**：
   - "下班前"、"下班后"、"开会前"、"开会后"等模糊时间节点必须保留在任务标题中
   - 根据上下文推断基准时间（如"五点才下班"意味着下班时间是17:00）
   - 模糊时间任务的截止日期使用基准时间
3. **时间转换规则**：
   - "八点"在日常语境中（如遛狗、吃饭、运动）通常指晚上8点（20:00），除非有明确说明是上午
   - 明确时段词："早上"、"上午"、"早晨"、"清晨" → 上午时间；"下午"、"晚上"、"傍晚"、"夜里" → 下午/晚上时间
   - 数字时间如"5点"、"18:00"等，结合上下文判断时段
4. **日期处理**：
   - "今天" → 当天（{today}）
   - "明天" → 次日（{tomorrow}）
   - "后天" → 第三天
   - "下周" → 7天后
   - 无明确日期时默认使用当天

### 三、标题生成规则
1. **标题长度**：严格控制在{self.config.max_title_length}个字符以内
2. **标题结构**：必须包含核心动作和对象（如"交方案给主管"而非"交给主管"）
3. **保留关键信息**：保留模糊时间节点（如"下班前"）和重要修饰词
4. **简练关键**：去除冗余词，只保留最核心的动宾结构

### 四、工具使用策略
- **多个任务**：当文本中包含2个或以上任务时，使用 `create_reminders` 工具批量创建
- **单个任务**：当文本中只有1个任务时，使用 `create_reminder` 工具创建

### 五、输出格式要求
- 截止日期必须为 YYYY-MM-DD HH:MM 格式
- 使用当前日期作为基准日期

## 详细示例

### 示例1：多任务场景
输入："五点才下班，下班前要把方案交给主管，下班后去烤肉店吃点烤肉，八点记得遛狗"

分析：
- "五点才下班"：背景信息，下班时间为17:00
- "下班前要把方案交给主管"：任务1，标题"下班前交方案给主管"，截止时间17:00
- "下班后去烤肉店吃点烤肉"：任务2，标题"下班后吃烤肉"，截止时间17:00
- "八点记得遛狗"：任务3，标题"八点遛狗"，截止时间20:00（根据语境判断为晚上8点）

处理：调用 create_reminders 工具，包含3个任务

### 示例2：单任务场景
输入："明天下午三点开会"

分析：
- "明天下午三点开会"：任务，标题"下午三点开会"，截止时间为明天15:00

处理：调用 create_reminder 工具

### 示例3：复杂时间场景
输入："今天早点回家，晚上八点半记得给妈妈打电话"

分析：
- "今天早点回家"：任务1，标题"早点回家"，截止时间为当天合理时间
- "晚上八点半记得给妈妈打电话"：任务2，标题"晚上八点半给妈妈打电话"，截止时间20:30

处理：调用 create_reminders 工具，包含2个任务

## 输出要求
- 你必须使用工具调用，不能直接输出任务列表
- 严格按照工具定义的参数格式输出
"""
        
        # 添加系统消息
        all_messages = [AIMessage(content=system_prompt)] + list(messages)
        
        # 调用LLM（带工具）
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
        
        # 检查是否有工具调用（需要继续执行工具）
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info("Tool calls detected, continuing to tool execution")
            return {}
        
        # 检查是否是工具执行结果
        if last_message.type == "tool" and hasattr(last_message, "content") and last_message.content:
            logger.info("Tool execution result found")
            content = last_message.content
            
            # 解析工具返回的结果
            if isinstance(content, dict) and "tasks" in content:
                # 工具返回了任务列表
                return {
                    "task_extracted": True,
                    "result": content
                }
            elif isinstance(content, list):
                # 工具返回了任务列表（直接返回列表）
                return {
                    "task_extracted": True,
                    "result": {"tasks": content}
                }
            elif isinstance(content, str) and content.startswith("tasks="):
                # 工具返回了字符串格式的结果，包含任务
                return {
                    "task_extracted": True,
                    "result": {"content": content}
                }
        
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
        
        使用简单处理：创建一个包含原始文本的任务
        
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
        
        text = last_user_message.content
        logger.info(f"Fallback for: {text[:50]}...")
        
        # 简单处理：创建一个包含原始文本的任务
        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        due_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        tasks_list = [{
            "title": title,
            "due_date": due_date,
            "description": text
        }]
        
        logger.info(f"Fallback extracted 1 task")
        
        return {
            "task_extracted": True,
            "result": {"tasks": tasks_list}
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
        llm: LLM实例（可选）
        
    Returns:
        TaskWorkflow: 任务工作流实例
    """
    return TaskWorkflow(llm=llm)