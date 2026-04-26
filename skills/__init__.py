"""Skills package - 可复用技能模块"""
from .base import SkillBase, SkillConfig
from .llm import LLMSkill
from .debate import DebateSkill
from .obsidian import ObsidianSkill

__all__ = [
    "SkillBase",
    "SkillConfig",
    "LLMSkill",
    "DebateSkill",
    "ObsidianSkill",
]