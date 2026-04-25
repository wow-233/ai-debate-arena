"""
Obsidian 写入服务 - 辩论报告保存为 Markdown
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import frontmatter
import logging

from ..core.config import Config
from ..models.debate import DebateReport, AgentRole

logger = logging.getLogger(__name__)


class ObsidianWriter:
    """Obsidian Markdown 写入器"""
    
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or Config.get_obsidian_path())
        self.debate_dir = self.vault_path / "10 - Debates"
        self.template_dir = self.vault_path / "99 - Meta" / "Templates"
        
        # 确保目录存在
        self.debate_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_agent_name(self, agent: AgentRole) -> str:
        """获取角色中文名"""
        names = {
            AgentRole.INVESTOR: "投资人",
            AgentRole.TECH_EXPERT: "技术专家",
            AgentRole.LEGAL: "法务合规",
        }
        return names.get(agent, str(agent))
    
    def _get_agent_section(self, agent: AgentRole) -> str:
        """获取角色章节标识"""
        icons = {
            AgentRole.INVESTOR: "👔",
            AgentRole.TECH_EXPERT: "🔧",
            AgentRole.LEGAL: "⚖️",
        }
        return icons.get(agent, "📌")
    
    def _build_frontmatter(self, report: DebateReport) -> dict:
        """构建 YAML frontmatter"""
        return {
            "title": f"AI辩论: {report.topic}",
            "date": report.created_at.strftime("%Y-%m-%d"),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "type": "debate_report",
            "tags": ["debate", "ai"],
            "participants": [a.value for a in report.participants],
            "topic": report.topic,
            "related": ["[[Business-Hub]]", "[[Tech-Hub]]"],
            "round": report.rounds,
            "status": report.status.value,
        }
    
    def _build_content(self, report: DebateReport) -> str:
        """构建 Markdown 内容"""
        lines = []
        
        # 标题
        lines.append(f"# AI辩论: {report.topic}\n")
        
        # 元信息
        lines.append(f"**日期**: {report.created_at.strftime('%Y-%m-%d %H:%M')}  ")
        lines.append(f"**轮次**: {report.rounds}  ")
        lines.append(f"**状态**: {report.status.value}\n")
        
        participants_str = "、".join([
            f"{self._get_agent_section(a)} {self._get_agent_name(a)}"
            for a in report.participants
        ])
        lines.append(f"**参与角色**: {participants_str}\n")
        
        lines.append("---\n")
        
        # 执行摘要
        lines.append("## 📊 执行摘要\n")
        if report.final_summary:
            lines.append(report.final_summary)
        else:
            lines.append("*辩论总结生成中...*")
        lines.append("\n")
        
        # 各角色观点
        for agent in report.participants:
            analysis = report.analyses.get(agent)
            if not analysis:
                continue
            
            section_icon = self._get_agent_section(agent)
            agent_name = self._get_agent_name(agent)
            
            lines.append(f"## {section_icon} {agent_name}观点\n")
            
            # 初始分析
            lines.append("### 初始分析\n")
            if analysis.initial_analysis:
                lines.append(analysis.initial_analysis)
            else:
                lines.append("*待分析*")
            lines.append("\n")
            
            # 辩论要点
            if analysis.debate_points:
                lines.append("### 辩论要点\n")
                for i, point in enumerate(analysis.debate_points, 1):
                    lines.append(f"{i}. {point}")
                lines.append("\n")
            
            # 最终总结
            if analysis.final_summary:
                lines.append("### 最终总结\n")
                lines.append(analysis.final_summary)
                lines.append("\n")
            
            lines.append("---\n")
        
        # 最终结论
        lines.append("## 🎯 最终结论\n")
        if report.final_summary:
            lines.append(report.final_summary)
        else:
            lines.append("*综合各方观点的结论生成中...*")
        lines.append("\n")
        
        # 辩论记录
        if report.debate_rounds:
            lines.append("## 📝 辩论记录\n")
            for round_data in report.debate_rounds:
                lines.append(f"### 第{round_data.round_number}轮 - {self._get_agent_name(round_data.agent)}\n")
                lines.append(round_data.content)
                lines.append(f"\n*时间: {round_data.timestamp.strftime('%H:%M:%S')}*\n")
                lines.append("---\n")
        
        return "\n".join(lines)
    
    def save_debate(self, report: DebateReport) -> Path:
        """保存辩论报告到 Obsidian"""
        # 生成文件名
        date_str = report.created_at.strftime("%Y-%m-%d")
        topic_slug = "".join(c if c.isalnum() else "-" for c in report.topic)[:50]
        filename = f"debate-{date_str}-{topic_slug}.md"
        
        # 按月份组织目录
        month_dir = self.debate_dir / report.created_at.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = month_dir / filename
        
        # 构建 frontmatter
        frontmatter_dict = self._build_frontmatter(report)
        
        # 构建内容
        content = self._build_content(report)
        
        # 写入文件
        post = frontmatter.Post(content)
        post.metadata = frontmatter_dict
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
        
        logger.info(f"辩论报告已保存: {file_path}")
        
        # 更新报告的路径
        report.obsidian_path = str(file_path)
        
        return file_path
    
    def create_from_template(self, template_name: str = "debate-report.md") -> Path:
        """从模板创建辩论报告"""
        template_path = self.template_dir / template_name
        return template_path


# 全局实例
_writer: Optional[ObsidianWriter] = None


def get_obsidian_writer(vault_path: str = None) -> ObsidianWriter:
    """获取 Obsidian 写入器单例"""
    global _writer
    if _writer is None:
        _writer = ObsidianWriter(vault_path)
    return _writer