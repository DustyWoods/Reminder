import json
import logging
import re
from typing import Optional
from openai import OpenAI

from config import settings
from models import ReminderResponse
from utils import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    LLM 服务类

    负责：
    - 从识别文本中提取任务信息
    - 调用 LLM 的 Function Call 功能
    """

    def __init__(self):
        self.client: Optional[OpenAI] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """初始化 OpenAI 客户端"""
        if settings.deepseek_api_key and settings.deepseek_api_key != "your_api_key_here":
            self.client = OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
            logger.info("LLM client initialized successfully")
        else:
            logger.warning("LLM client not initialized: no valid API key")

    def is_available(self) -> bool:
        """检查 LLM 服务是否可用"""
        return self.client is not None

    def _extract_json_from_content(self, content: str) -> dict:
        """
        从内容中提取 JSON 数据

        支持从 markdown 代码块中提取 JSON
        """
        if not content:
            raise ValueError("内容为空")

        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试从 markdown 代码块中提取
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取裸的 JSON 对象
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从内容中提取 JSON: {content[:100]}")

    def _generate_fallback_reminder(self, text: str) -> ReminderResponse:
        """
        生成备用任务信息

        当 LLM 提取失败时使用
        """
        logger.warning(f"使用备用任务信息，原始文本: {text}")
        return ReminderResponse(
            title=text[:50] if len(text) > 50 else text,
            due_date="2026-06-01 12:00",
            description=f"原始输入: {text}"
        )

    def extract_reminder(self, text: str) -> ReminderResponse:
        """
        从识别文本中提取任务信息

        Args:
            text: 语音识别的文本

        Returns:
            ReminderResponse: 提取的任务信息

        Raises:
            ValueError: 当提取失败时
        """
        if not self.client:
            raise ValueError("LLM client not available")

        # 定义 Function Call 工具
        tool_definition = {
            "type": "function",
            "function": {
                "name": "create_reminder",
                "description": "从自然语言中分析并提取提醒任务信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "任务的简短标题"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "任务的截止日期和时间，格式为 YYYY-MM-DD HH:MM"
                        },
                        "description": {
                            "type": "string",
                            "description": "任务的详细描述"
                        }
                    },
                    "required": ["title", "due_date", "description"]
                }
            }
        }

        try:
            response = self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个智能助手，专门从自然语言中分析并提取任务提醒信息。请使用 create_reminder 工具来完成此任务。"
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                tools=[tool_definition],
                tool_choice={"type": "function", "function": {"name": "create_reminder"}}
            )

            # 检查是否有工具调用
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls and tool_calls[0].function.arguments:
                reminder_data = json.loads(tool_calls[0].function.arguments)
            else:
                content = response.choices[0].message.content
                if not content:
                    logger.warning("模型未返回内容，使用备用任务信息")
                    return self._generate_fallback_reminder(text)

                try:
                    reminder_data = self._extract_json_from_content(content)
                except ValueError:
                    logger.warning(f"无法解析模型返回内容，使用备用任务信息: {content[:100]}")
                    return self._generate_fallback_reminder(text)

            # 验证必需字段
            if not all(key in reminder_data for key in ["title", "due_date", "description"]):
                missing_keys = [k for k in ["title", "due_date", "description"] if k not in reminder_data]
                logger.warning(f"任务信息缺少字段: {missing_keys}，使用备用任务信息")
                return self._generate_fallback_reminder(text)

            return ReminderResponse(
                title=reminder_data["title"],
                due_date=reminder_data["due_date"],
                description=reminder_data["description"]
            )

        except ValueError as e:
            logger.error(f"值错误: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"提取提醒时发生未预期错误: {str(e)}")
            return self._generate_fallback_reminder(text)


# 全局 LLM 服务实例
llm_service = LLMService()
