"""
辩论引擎 - 多智能体辩论核心逻辑
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Callable, AsyncGenerator, Dict, Any
from enum import Enum
import logging

from ..core.llm import get_llm_client
from ..core.router import ModelRouter, ModelTier
from ..models.debate import (
    DebateReport, DebateRound, AgentAnalysis, AgentRole,
    DebateStatus, DebateStreamEvent
)
from ..models.agent import get_agent_system_prompt, get_agent_description
from .obsidian_reader import get_obsidian_reader

logger = logging.getLogger(__name__)


class DebatePhase(str, Enum):
    """辩论阶段"""
    PARALLEL_ANALYSIS = "parallel_analysis"  # 并行分析
    SERIAL_DEBATE = "serial_debate"          # 串行辩论
    CONCLUSION = "conclusion"                 # 总结


class DebateEngine:
    """辩论引擎"""
    
    # 辩论顺序（串行阶段）
    DEBATE_SEQUENCE = [
        AgentRole.INVESTOR,
        AgentRole.TECH_EXPERT,
        AgentRole.LEGAL,
    ]
    
    def __init__(self):
        self.llm = get_llm_client()
        self.obsidian_reader = get_obsidian_reader()
    
    async def _emit_event(
        self,
        callback: Optional[Callable],
        event: DebateStreamEvent
    ) -> None:
        """发送 SSE 事件"""
        if callback:
            await callback(event)
    
    async def _build_context(self, context_paths: List[str]) -> str:
        """构建辩论上下文"""
        if not context_paths:
            return ""
        return self.obsidian_reader.build_context(context_paths)
    
    async def _parallel_analysis(
        self,
        report: DebateReport,
        context: str,
        emit_callback: Optional[Callable] = None,
    ) -> Dict[AgentRole, AgentAnalysis]:
        """并行初始分析"""
        results: Dict[AgentRole, AgentAnalysis] = {}
        
        async def analyze_agent(agent: AgentRole) -> tuple:
            prompt = self._build_analysis_prompt(agent, report.topic, context)
            system_prompt = get_agent_system_prompt(agent)
            
            analysis = await self.llm.chat_with_system(
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=0.7,
            )
            
            await self._emit_event(emit_callback, DebateStreamEvent(
                event_type="analysis",
                round=0,
                agent=agent.value,
                content=analysis,
            ))
            
            return agent, AgentAnalysis(
                agent=agent,
                initial_analysis=analysis,
            )
        
        # 并行执行所有分析
        tasks = [analyze_agent(agent) for agent in report.participants]
        completed = await asyncio.gather(*tasks)
        
        for agent, analysis in completed:
            results[agent] = analysis
            report.analyses[agent] = analysis
        
        return results
    
    def _build_analysis_prompt(self, agent: AgentRole, topic: str, context: str) -> str:
        """构建分析提示词"""
        prompt = f"## 辩论主题\n{topic}\n\n"
        
        if context:
            prompt += f"## 参考资料\n{context}\n\n"
        
        prompt += """## 任务
请作为该角色对上述主题进行深入分析，包括：
1. 你的核心观点和立场
2. 主要论据和数据支撑
3. 潜在的风险和挑战
4. 建设性建议

请用简洁专业的语言输出你的分析结果（建议 300-500 字）。
"""
        return prompt
    
    async def _serial_debate_round(
        self,
        report: DebateReport,
        round_num: int,
        all_analyses: Dict[AgentRole, AgentAnalysis],
        emit_callback: Optional[Callable] = None,
    ) -> List[DebateRound]:
        """串行辩论一轮"""
        rounds = []
        
        # 获取前几轮的辩论内容
        prior_rounds = self._get_prior_rounds_content(report, round_num)
        
        for agent in self.DEBATE_SEQUENCE:
            # 获取其他角色的观点
            other_analyses = self._get_other_analyses(all_analyses, agent)
            
            prompt = self._build_debate_prompt(
                agent, report.topic, other_analyses, prior_rounds, round_num
            )
            system_prompt = get_agent_system_prompt(agent)
            
            content = await self.llm.chat_with_system(
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=0.8,
            )
            
            debate_round = DebateRound(
                round_number=round_num,
                agent=agent,
                content=content,
            )
            rounds.append(debate_round)
            report.debate_rounds.append(debate_round)
            
            # 提取辩论要点
            self._extract_debate_points(report, agent, content)
            
            await self._emit_event(emit_callback, DebateStreamEvent(
                event_type="debate",
                round=round_num,
                agent=agent.value,
                content=content,
            ))
            
            # 模拟思考时间
            await asyncio.sleep(0.5)
        
        return rounds
    
    def _get_prior_rounds_content(self, report: DebateReport, current_round: int) -> str:
        """获取之前轮次的辩论内容"""
        lines = []
        for round_data in report.debate_rounds:
            if round_data.round_number < current_round:
                lines.append(f"### 第{round_data.round_number}轮 - {round_data.agent.value}")
                lines.append(round_data.content)
                lines.append("")
        return "\n".join(lines) if lines else "（暂无）"
    
    def _get_other_analyses(
        self,
        analyses: Dict[AgentRole, AgentAnalysis],
        current_agent: AgentRole,
    ) -> str:
        """获取其他角色的分析"""
        lines = []
        for agent, analysis in analyses.items():
            if agent != current_agent:
                lines.append(f"## {agent.value} 的观点\n{analysis.initial_analysis}\n")
        return "\n".join(lines) if lines else "（暂无）"
    
    def _build_debate_prompt(
        self,
        agent: AgentRole,
        topic: str,
        other_analyses: str,
        prior_rounds: str,
        round_num: int,
    ) -> str:
        """构建辩论提示词"""
        prompt = f"## 辩论主题\n{topic}\n\n"
        prompt += f"## 第 {round_num} 轮辩论\n\n"
        
        prompt += "## 其他角色的观点\n" + other_analyses + "\n\n"
        
        prompt += "## 历史辩论记录\n" + prior_rounds + "\n\n"
        
        prompt += f"""## 任务
这是第 {round_num} 轮辩论。请你：
1. 回应其他角色的观点
2. 提出新的论据或反驳
3. 坚守你的核心立场

请用专业、有说服力的语言输出你的观点。
"""
        return prompt
    
    def _extract_debate_points(
        self,
        report: DebateReport,
        agent: AgentRole,
        content: str,
    ) -> None:
        """从辩论内容中提取要点"""
        analysis = report.analyses.get(agent)
        if analysis:
            # 简单策略：按句号分割，取前几个
            sentences = [s.strip() for s in content.split("。") if len(s.strip()) > 20]
            # 取最重要的 3-5 个点
            points = sentences[:5]
            analysis.debate_points.extend(points)
    
    async def _generate_conclusion(
        self,
        report: DebateReport,
        emit_callback: Optional[Callable] = None,
    ) -> str:
        """生成最终总结"""
        # 汇总所有分析
        all_content = []
        for agent, analysis in report.analyses.items():
            all_content.append(f"## {agent.value} 分析\n{analysis.initial_analysis}\n")
            if analysis.debate_points:
                all_content.append(f"辩论要点: {'; '.join(analysis.debate_points[:3])}\n")
        
        for round_data in report.debate_rounds:
            all_content.append(f"## 第{round_data.round_number}轮 - {round_data.agent.value}\n")
            all_content.append(round_data.content)
        
        prompt = f"""## 辩论主题
{report.topic}

## 辩论内容汇总
{"".join(all_content)}

## 任务
作为辩论主持人，请整合所有观点，生成一份结构化的辩论总结：
1. **核心争议点**：各方的主要分歧
2. **共识领域**：各方达成的一致
3. **风险提示**：需要注意的关键风险
4. **建议行动**：综合建议

请用专业、客观的语气输出总结。
"""
        
        system_prompt = """你是一位专业的主持人，擅长整合多方观点，形成客观全面的总结。"""
        
        conclusion = await self.llm.chat_with_system(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=0.6,
        )
        
        report.final_summary = conclusion
        report.status = DebateStatus.COMPLETED
        report.completed_at = datetime.now()
        
        await self._emit_event(emit_callback, DebateStreamEvent(
            event_type="conclusion",
            round=report.rounds,
            content=conclusion,
        ))
        
        return conclusion
    
    async def run_debate(
        self,
        topic: str,
        context_paths: List[str] = None,
        rounds: int = 3,
        model_tier: str = "auto",
        emit_callback: Optional[Callable] = None,
    ) -> DebateReport:
        """运行完整辩论"""
        # 初始化报告
        report = DebateReport(
            id=str(uuid.uuid4()),
            topic=topic,
            participants=[AgentRole.INVESTOR, AgentRole.TECH_EXPERT, AgentRole.LEGAL],
            rounds=rounds,
            status=DebateStatus.ANALYZING,
        )
        
        # 构建上下文
        context = await self._build_context(context_paths or [])
        
        try:
            # 阶段 1: 并行分析
            report.status = DebateStatus.ANALYZING
            await self._emit_event(emit_callback, DebateStreamEvent(
                event_type="analysis",
                round=0,
                content="开始并行分析...",
            ))
            
            all_analyses = await self._parallel_analysis(report, context, emit_callback)
            
            # 阶段 2: 串行辩论
            report.status = DebateStatus.DEBATING
            for round_num in range(1, rounds + 1):
                await self._emit_event(emit_callback, DebateStreamEvent(
                    event_type="debate",
                    round=round_num,
                    content=f"开始第 {round_num} 轮辩论...",
                ))
                
                await self._serial_debate_round(
                    report, round_num, all_analyses, emit_callback
                )
            
            # 阶段 3: 总结
            report.status = DebateStatus.CONCLUDING
            await self._emit_event(emit_callback, DebateStreamEvent(
                event_type="conclusion",
                round=rounds,
                content="生成最终总结...",
            ))
            
            await self._generate_conclusion(report, emit_callback)
            
            # 完成
            report.status = DebateStatus.COMPLETED
            await self._emit_event(emit_callback, DebateStreamEvent(
                event_type="done",
                round=rounds,
                content="辩论完成",
            ))
            
        except Exception as e:
            logger.error(f"辩论执行失败: {e}")
            report.status = DebateStatus.FAILED
            await self._emit_event(emit_callback, DebateStreamEvent(
                event_type="error",
                content=str(e),
            ))
            raise
        
        return report


# 全局实例
_engine: Optional[DebateEngine] = None


def get_debate_engine() -> DebateEngine:
    """获取辩论引擎单例"""
    global _engine
    if _engine is None:
        _engine = DebateEngine()
    return _engine