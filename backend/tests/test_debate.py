"""
辩论引擎测试
"""
import pytest
from app.models.debate import DebateReport, AgentRole


def test_debate_report_creation():
    """测试辩论报告创建"""
    report = DebateReport(
        id="test-123",
        topic="测试主题",
        participants=[AgentRole.INVESTOR, AgentRole.TECH_EXPERT, AgentRole.LEGAL],
        rounds=3,
    )
    
    assert report.id == "test-123"
    assert report.topic == "测试主题"
    assert len(report.participants) == 3
    assert report.rounds == 3


def test_agent_roles():
    """测试角色枚举"""
    assert AgentRole.INVESTOR.value == "investor"
    assert AgentRole.TECH_EXPERT.value == "tech_expert"
    assert AgentRole.LEGAL.value == "legal"