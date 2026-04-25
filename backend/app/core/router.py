"""
模型路由器 - 根据任务复杂度选择合适模型
"""
from enum import Enum
from typing import Optional
import logging

from ..core.config import Config

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """模型层级"""
    FAST = "fast"          # 简单任务
    BALANCED = "balanced"   # 平衡
    DEEP = "deep"         # 复杂任务
    AUTO = "auto"         # 自动选择


class ModelRouter:
    """模型路由器"""
    
    # 任务复杂度评估关键词
    COMPLEX_KEYWORDS = [
        "分析", "评估", "对比", "论证", "推理",
        "详细", "深入", "全面", "复杂",
        "security", "legal", "compliance", "architecture",
        "analyze", "evaluate", "compare", "argue"
    ]
    
    SIMPLE_KEYWORDS = [
        "摘要", "总结", "列出", "翻译", "格式化",
        "summarize", "list", "translate", "format"
    ]
    
    @classmethod
    def get_model(cls, tier: str = "auto", task_description: str = "") -> str:
        """
        根据层级或任务描述获取模型
        
        Args:
            tier: 模型层级 (fast/balanced/deep/auto)
            task_description: 任务描述，用于自动判断
            
        Returns:
            模型名称
        """
        if tier == ModelTier.AUTO:
            tier = cls._estimate_tier(task_description)
        
        tier = tier.lower()
        
        if tier == ModelTier.FAST:
            return Config.MODEL_FAST
        elif tier == ModelTier.DEEP:
            return Config.MODEL_DEEP
        else:  # balanced or default
            return Config.MODEL_BALANCED
    
    @classmethod
    def _estimate_tier(cls, description: str) -> str:
        """根据任务描述估计复杂度"""
        desc_lower = description.lower()
        
        # 简单任务
        for keyword in cls.SIMPLE_KEYWORDS:
            if keyword in desc_lower:
                return ModelTier.FAST
        
        # 复杂任务
        for keyword in cls.COMPLEX_KEYWORDS:
            if keyword in desc_lower:
                return ModelTier.DEEP
        
        # 默认平衡
        return ModelTier.BALANCED
