"""
LLM 通用工具函数

- parse_llm_json: 从 LLM 响应中提取 JSON
- build_llm: 创建 ChatOpenAI 实例
"""
import json
import re
from typing import Optional
from langchain_openai import ChatOpenAI

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import get_logger

logger = get_logger(__name__)


def parse_llm_json(content: str) -> Optional[dict | list]:
    """从 LLM 响应中提取 JSON，处理 markdown 代码块等干扰"""
    content = content.strip()
    content = re.sub(r'^```(?:json)?\s*', '', content)
    content = re.sub(r'\s*```$', '', content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        for pattern in [r'\[.*\]', r'\{.*\}']:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue
        return None


def build_llm(
    model: str = None,
    api_key: str = None,
    base_url: str = None,
    temperature: float = 0.1,
    max_tokens: int = 1024
) -> ChatOpenAI:
    """创建 ChatOpenAI 实例"""
    from agent.config import get_config
    config = get_config()
    return ChatOpenAI(
        model=model or config.effective_model,
        api_key=api_key or config.effective_api_key,
        base_url=base_url or config.effective_base_url,
        temperature=temperature or config.llm_temperature,
        max_tokens=max_tokens or config.llm_max_tokens
    )