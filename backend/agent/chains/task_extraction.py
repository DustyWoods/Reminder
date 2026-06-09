"""
任务提取链 - 优化版

核心优化：
1. 减少静态规则处理，让LLM承担主要任务提取工作
2. 优化提示词，增强任务拆分和时间分析能力
3. 简化任务标题生成逻辑
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

from models import ReminderResponse, ReminderListResponse
from agent.config import get_config
from utils import get_logger

logger = get_logger(__name__)


class TaskExtractionChain:
    """
    任务提取链 - 使用LLM从自然语言中智能提取任务信息
    
    核心特性：
    - 多任务识别：自动识别文本中的多个独立任务
    - 智能时间分析：结合上下文准确解析时间
    - 简练标题生成：生成包含核心动宾结构的简洁标题
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        初始化任务提取链
        
        Args:
            llm: LLM实例（可选，如果不提供则使用配置创建）
        """
        self.config = get_config()
        self.llm = llm or self._create_llm()
        self.chain = self._build_chain()
    
    def _create_llm(self) -> ChatOpenAI:
        """创建LLM实例"""
        return ChatOpenAI(
            model=self.config.effective_model,
            api_key=self.config.effective_api_key,
            base_url=self.config.effective_base_url,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
    
    def _build_chain(self) -> RunnableSequence:
        """
        构建任务提取链
        
        Returns:
            RunnableSequence: 可执行的链
        """
        # 优化后的系统提示词 - 更清晰、更详细的指令
        system_prompt = """
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
   - "今天" → 当天
   - "明天" → 次日
   - "后天" → 第三天
   - "下周" → 7天后
   - 无明确日期时默认使用当天

### 三、标题生成规则
1. **标题长度**：严格控制在{max_title_length}个字符以内
2. **标题结构**：必须包含核心动作和对象（如"交方案给主管"而非"交给主管"）
3. **保留关键信息**：保留模糊时间节点（如"下班前"）和重要修饰词
4. **简练关键**：去除冗余词，只保留最核心的动宾结构

### 四、输出格式要求
- 截止日期必须为 YYYY-MM-DD HH:MM 格式
- 使用当前日期作为基准日期
- 严格按照JSON格式输出，不要输出其他文字说明

## 详细示例

### 示例1：多任务场景
输入："五点才下班，下班前要把方案交给主管，下班后去烤肉店吃点烤肉，八点记得遛狗"

分析：
- "五点才下班"：背景信息，下班时间为17:00
- "下班前要把方案交给主管"：任务1，标题"下班前交方案给主管"，截止时间17:00
- "下班后去烤肉店吃点烤肉"：任务2，标题"下班后吃烤肉"，截止时间17:00
- "八点记得遛狗"：任务3，标题"八点遛狗"，截止时间20:00（根据语境判断为晚上8点）

输出：
{{
  "tasks": [
    {{
      "title": "下班前交方案给主管",
      "due_date": "{today} 17:00",
      "description": "下班前要把方案交给主管"
    }},
    {{
      "title": "下班后吃烤肉",
      "due_date": "{today} 17:00",
      "description": "下班后去烤肉店吃点烤肉"
    }},
    {{
      "title": "八点遛狗",
      "due_date": "{today} 20:00",
      "description": "八点记得遛狗"
    }}
  ]
}}

### 示例2：单任务场景
输入："明天下午三点开会"

分析：
- "明天下午三点开会"：任务，标题"下午三点开会"，截止时间为明天15:00

输出：
{{
  "tasks": [
    {{
      "title": "下午三点开会",
      "due_date": "{tomorrow} 15:00",
      "description": "明天下午三点开会"
    }}
  ]
}}

### 示例3：复杂时间场景
输入："今天早点回家，晚上八点半记得给妈妈打电话"

分析：
- "今天早点回家"：任务1，标题"早点回家"，截止时间为当天合理时间
- "晚上八点半记得给妈妈打电话"：任务2，标题"晚上八点半给妈妈打电话"，截止时间20:30

输出：
{{
  "tasks": [
    {{
      "title": "早点回家",
      "due_date": "{today} 18:00",
      "description": "今天早点回家"
    }},
    {{
      "title": "晚上八点半给妈妈打电话",
      "due_date": "{today} 20:30",
      "description": "晚上八点半记得给妈妈打电话"
    }}
  ]
}}

## 输出格式
请严格按照以下JSON格式输出：
{{
  "tasks": [
    {{
      "title": "任务1的简短标题",
      "due_date": "YYYY-MM-DD HH:MM",
      "description": "任务1的完整描述"
    }},
    {{
      "title": "任务2的简短标题",
      "due_date": "YYYY-MM-DD HH:MM",
      "description": "任务2的完整描述"
    }}
  ]
}}

注意事项：
1. 只输出JSON，不要输出其他文字说明
2. 确保JSON格式正确，引号使用双引号
3. 如果没有识别到任何有效任务，返回空数组
"""
        
        # 获取当前日期用于提示词中的示例
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        # 使用partial注入配置参数和日期
        prompt_with_config = prompt.partial(
            max_title_length=str(self.config.max_title_length),
            today=today,
            tomorrow=tomorrow
        )
        
        parser = JsonOutputParser(pydantic_object=ReminderListResponse)
        
        chain = prompt_with_config | self.llm | parser
        return chain
    
    def invoke(self, text: str) -> List[ReminderResponse]:
        """
        执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info(f"Extracting tasks from: {text[:50]}...")
        
        try:
            result = self.chain.invoke({"input": text})
            
            if isinstance(result, ReminderListResponse):
                tasks = result.tasks
                if tasks and len(tasks) > 0:
                    logger.info(f"Successfully extracted {len(tasks)} tasks")
                    return tasks
            
            if isinstance(result, dict):
                tasks_data = result.get("tasks", [])
                if isinstance(tasks_data, list) and len(tasks_data) > 0:
                    logger.info(f"Successfully extracted {len(tasks_data)} tasks")
                    return [ReminderResponse(**task) for task in tasks_data]
            
            logger.warning("No tasks extracted, using fallback")
            return self._fallback(text)
            
        except Exception as e:
            logger.error(f"Task extraction failed: {str(e)}, using fallback")
            return self._fallback(text)
    
    async def ainvoke(self, text: str) -> List[ReminderResponse]:
        """
        异步执行任务提取
        
        Args:
            text: 用户输入的自然语言文本
            
        Returns:
            List[ReminderResponse]: 提取的任务列表
        """
        logger.info(f"Async extracting tasks from: {text[:50]}...")
        
        try:
            result = await self.chain.ainvoke({"input": text})
            
            if isinstance(result, ReminderListResponse):
                tasks = result.tasks
                if tasks and len(tasks) > 0:
                    logger.info(f"Successfully extracted {len(tasks)} tasks")
                    return tasks
            
            if isinstance(result, dict):
                tasks_data = result.get("tasks", [])
                if isinstance(tasks_data, list) and len(tasks_data) > 0:
                    logger.info(f"Successfully extracted {len(tasks_data)} tasks")
                    return [ReminderResponse(**task) for task in tasks_data]
            
            logger.warning("No tasks extracted, using fallback")
            return self._fallback(text)
            
        except Exception as e:
            logger.error(f"Async task extraction failed: {str(e)}, using fallback")
            return self._fallback(text)
    
    def _fallback(self, text: str) -> List[ReminderResponse]:
        """
        备用方案：当LLM提取失败时使用
        
        Args:
            text: 用户输入文本
            
        Returns:
            List[ReminderResponse]: 任务列表
        """
        logger.info(f"Using fallback for: {text[:50]}...")
        
        # 简单处理：创建一个包含原始文本的任务
        title = text[:self.config.max_title_length] if len(text) > self.config.max_title_length else text
        due_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return [ReminderResponse(
            title=title,
            due_date=due_date,
            description=text
        )]