"""
Debate 技能 - 多智能体辩论
"""
import asyncio
import logging
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field

from .base import SkillBase, SkillConfig, RunnableSkill, SkillResult
from .llm import LLMSkill

logger = logging.getLogger(__name__)


class DebateRole(str, Enum):
    """辩论角色"""
    INVESTOR = "investor"
    TECH_EXPERT = "tech_expert"
    LEGAL = "legal"
    MODERATOR = "moderator"


# 角色系统提示
ROLE_PROMPTS = {
    DebateRole.INVESTOR: """你是一位经验丰富的投资人，10+年投资经验，擅长评估商业模式、市场潜力和团队能力。""",
    DebateRole.TECH_EXPERT: """你是一位资深技术专家，15+年软件开发经验，精通系统架构和云原生技术。""",
    DebateRole.LEGAL: """你是一位法务合规专家，10+年法务经验，服务过50+创业公司。""",
}


@dataclass
class DebateTurn:
    """辩论回合"""
    round_num: int
    role: DebateRole
    content: str
    timestamp: str = ""


@dataclass
class DebateState:
    """辩论状态"""
    id: str = ""
    topic: str = ""
    rounds: int = 3
    turns: List[DebateTurn] = field(default_factory=list)
    final_summary: str = ""


class DebateSkill(RunnableSkill):
    """辩论技能"""
    
    def __init__(
        self,
        llm: LLMSkill,
        roles: Optional[List[DebateRole]] = None,
        config: Optional[SkillConfig] = None
    ):
        super().__init__(config)
        self.llm = llm
        self.roles = roles or [DebateRole.INVESTOR, DebateRole.TECH_EXPERT, DebateRole.LEGAL]
        self._state: Optional[DebateState] = None
    
    async def run(
        self,
        topic: str,
        rounds: int = 3,
        context: Optional[str] = None,
        stream_callback: Optional[Callable] = None,
    ) -> DebateState:
        """运行辩论"""
        state = DebateState(
            id=str(uuid.uuid4()),
            topic=topic,
            rounds=rounds,
        )
        self._state = state
        
        # 并行初始分析
        if stream_callback:
            await stream_callback("analysis", "Starting parallel analysis...")
        
        initial_analyses = await self._parallel_analysis(topic, context, stream_callback)
        
        # 串行辩论
        for round_num in range(1, rounds + 1):
            if stream_callback:
                await stream_callback("debate", f"Round {round_num}/{rounds}")
            
            await self._serial_debate(round_num, initial_analyses, stream_callback)
        
        # 总结
        if stream_callback:
            await stream_callback("conclusion", "Generating summary...")
        
        state.final_summary = await self._generate_summary()
        
        return state
    
    async def _parallel_analysis(
        self,
        topic: str,
        context: Optional[str],
        callback: Optional[Callable]
    ) -> Dict[DebateRole, str]:
        """并行分析"""
        analyses = {}
        
        async def analyze(role: DebateRole):
            system_prompt = ROLE_PROMPTS[role]
            user_prompt = f"## 主题\n{topic}\n\n"
            if context:
                user_prompt += f"## 上下文\n{context}\n\n"
            user_prompt += "请进行深入分析（300-500字）。"
            
            result = await self.llm.chat(user_prompt, system_prompt=system_prompt)
            analyses[role] = result
            
            if callback:
                await callback(role.value, result)
            
            return role, result
        
        # 并行执行
        tasks = [analyze(role) for role in self.roles]
        results = await asyncio.gather(*tasks)
        
        return {role: analysis for role, analysis in results}
    
    async def _serial_debate(
        self,
        round_num: int,
        initial_analyses: Dict[DebateRole, str],
        callback: Optional[Callable]
    ) -> None:
        """串行辩论"""
        for role in self.roles:
            # 构建上下文
            other_views = "\n\n".join([
                f"## {r.value}\n{a}"
                for r, a in initial_analyses.items()
                if r != role
            ])
            
            prior_turns = "\n\n".join([
                f"### {t.role.value} (Round {t.round_num})\n{t.content}"
                for t in self._state.turns
                if t.round_num < round_num
            ])
            
            system_prompt = ROLE_PROMPTS[role]
            user_prompt = f"## 主题\n{self._state.topic}\n\n"
            user_prompt += f"## 其他观点\n{other_views}\n\n"
            if prior_turns:
                user_prompt += f"## 历史记录\n{prior_turns}\n\n"
            user_prompt += f"## 第 {round_num} 轮\n请回应并阐述你的观点。"
            
            content = await self.llm.chat(user_prompt, system_prompt=system_prompt)
            
            turn = DebateTurn(
                round_num=round_num,
                role=role,
                content=content,
            )
            self._state.turns.append(turn)
            
            if callback:
                await callback(role.value, content)
    
    async def _generate_summary(self) -> str:
        """生成总结"""
        all_content = "\n\n".join([
            f"## {turn.role.value}\n{turn.content}"
            for turn in self._state.turns
        ])
        
        prompt = f"""## 辩论主题
{self._state.topic}

## 辩论记录
{all_content}

## 任务
作为主持人，请总结各方观点，给出综合建议。
"""
        
        return await self.llm.chat(prompt)
    
    async def execute(self, topic: str, **kwargs) -> SkillResult:
        """执行辩论"""
        try:
            state = await self.run(topic, **kwargs)
            return SkillResult(
                success=True,
                data={
                    "id": state.id,
                    "topic": state.topic,
                    "final_summary": state.final_summary,
                    "turns_count": len(state.turns),
                }
            )
        except Exception as e:
            logger.error(f"Debate failed: {e}")
            return SkillResult(success=False, error=str(e))


# 别名
DebateRunner = DebateSkill