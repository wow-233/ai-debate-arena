"""
辩论数据模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """角色类型"""
    INVESTOR = "investor"           # 投资人
    TECH_EXPERT = "tech_expert"     # 技术专家
    LEGAL = "legal"                 # 法务合规
    MODERATOR = "moderator"         # 主持人/总结


class DebateStatus(str, Enum):
    """辩论状态"""
    PENDING = "pending"         # 待开始
    ANALYZING = "analyzing"     # 分析中
    DEBATING = "debating"      # 辩论中
    CONCLUDING = "concluding"   # 总结中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"          # 失败


class DebateRound(BaseModel):
    """辩论轮次"""
    round_number: int
    agent: AgentRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentAnalysis(BaseModel):
    """角色分析结果"""
    agent: AgentRole
    initial_analysis: str = ""
    debate_points: List[str] = Field(default_factory=list)
    final_summary: str = ""


class DebateReport(BaseModel):
    """辩论报告"""
    id: str
    topic: str
    status: DebateStatus = DebateStatus.PENDING
    participants: List[AgentRole] = Field(default_factory=list)
    rounds: int = 3
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # 分析结果
    analyses: Dict[AgentRole, AgentAnalysis] = Field(default_factory=dict)
    debate_rounds: List[DebateRound] = Field(default_factory=list)
    
    # 总结
    final_summary: str = ""
    
    # Obsidian 相关
    obsidian_path: Optional[str] = None


class DebateStartRequest(BaseModel):
    """开始辩论请求"""
    topic: str = Field(..., description="辩论主题")
    context_paths: List[str] = Field(default_factory=list, description="关联的 Obsidian 笔记路径")
    rounds: int = Field(default=3, description="辩论轮数", ge=1, le=10)
    model_tier: str = Field(default="auto", description="模型层级: auto/fast/balanced/deep")


class DebateStreamEvent(BaseModel):
    """辩论流式事件"""
    event_type: str  # analysis/debate/conclusion/done/error
    round: int = 0
    agent: Optional[str] = None
    content: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class DebateResponse(BaseModel):
    """辩论响应"""
    id: str
    topic: str
    status: DebateStatus
    progress: float = 0.0  # 0-1
    current_agent: Optional[str] = None
    message: str = ""
