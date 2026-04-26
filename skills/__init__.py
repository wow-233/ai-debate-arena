"""Skills package"""
__version__ = "1.0.0"

from .base import SkillBase, SkillConfig, RunnableSkill, SkillResult
from .llm import LLMSkill, MultiModelLLM
from .debate import DebateSkill, DebateRole, DebateState
from .obsidian import ObsidianSkill, NoteInfo

__all__ = [
    "SkillBase",
    "SkillConfig",
    "RunnableSkill",
    "SkillResult",
    "LLMSkill",
    "MultiModelLLM",
    "DebateSkill",
    "DebateRole",
    "DebateState",
    "ObsidianSkill",
    "NoteInfo",
]