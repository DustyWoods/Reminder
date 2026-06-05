"""
工具基类和注册表
"""
from typing import Optional, List, Type, Any, Callable
from abc import ABC, abstractmethod
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from utils import get_logger

logger = get_logger(__name__)


class BaseToolInput(BaseModel):
    """工具输入基类"""
    pass


class BaseCustomTool(BaseTool, ABC):
    """自定义工具基类"""
    
    args_schema: Type[BaseModel]
    
    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """执行工具"""
        pass
    
    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """异步执行工具（可选实现）"""
        return self._run(*args, **kwargs)


class ToolRegistry:
    """
    工具注册表
    
    单例模式，管理所有可用的工具
    """
    _instance: Optional["ToolRegistry"] = None
    _tools: dict[str, BaseTool] = {}
    
    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        注册工具
        
        Args:
            tool: 要注册的工具实例
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def register_function(
        self, 
        func: Callable, 
        name: str, 
        description: str,
        args_schema: Optional[Type[BaseModel]] = None
    ) -> None:
        """
        从函数注册工具
        
        Args:
            func: 工具函数
            name: 工具名称
            description: 工具描述
            args_schema: 参数 schema（可选）
        """
        tool = BaseCustomTool.create_tool(func, name, description, args_schema)
        self.register_tool(tool)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回 None
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有已注册的工具
        
        Returns:
            工具列表
        """
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """
        获取所有工具名称
        
        Returns:
            工具名称列表
        """
        return list(self._tools.keys())
    
    def clear_tools(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        logger.info("All tools cleared")
    
    def __len__(self) -> int:
        """获取工具数量"""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """检查工具是否已注册"""
        return name in self._tools


# 创建全局工具注册表实例
tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表实例"""
    return tool_registry
