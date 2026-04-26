"""
Skills 基础模块
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SkillConfig:
    """技能配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def as_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


class SkillBase(ABC):
    """技能基类"""
    
    def __init__(self, config: Optional[SkillConfig] = None):
        self.config = config or SkillConfig(name=self.__class__.__name__)
        self._initialized = False
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def version(self) -> str:
        return self.config.version
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> SkillResult:
        """执行技能"""
        pass
    
    async def initialize(self) -> None:
        """初始化技能"""
        if not self._initialized:
            await self._on_initialize()
            self._initialized = True
    
    async def _on_initialize(self) -> None:
        """实际初始化逻辑"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(version={self.version})"


class RunnableSkill(SkillBase):
    """可运行的技能"""
    
    @abstractmethod
    async def run(self, input_data: Any, **kwargs) -> Any:
        """运行技能"""
        pass
    
    async def execute(self, input_data: Any, **kwargs) -> SkillResult:
        """执行并返回结果"""
        try:
            await self.initialize()
            result = await self.run(input_data, **kwargs)
            return SkillResult(
                success=True,
                data=result,
                metadata={"timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )