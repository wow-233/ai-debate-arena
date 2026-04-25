"""
辩论 API 路由
"""
import asyncio
import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
import logging

from ..models.debate import (
    DebateStartRequest, DebateResponse, DebateReport,
    DebateStreamEvent, AgentRole, DebateStatus
)
from ..services.debate_engine import get_debate_engine
from ..services.obsidian_writer import get_obsidian_writer
from ..services.obsidian_reader import get_obsidian_reader, NoteInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debate", tags=["辩论"])

# 内存存储（生产环境应使用数据库）
_debates: dict = {}


async def debate_event_generator(debate_id: str):
    """辩论 SSE 事件生成器"""
    report = _debates.get(debate_id)
    if not report:
        return
    
    engine = get_debate_engine()
    obsidian_writer = get_obsidian_writer()
    
    async def emit_callback(event: DebateStreamEvent):
        """发送事件的回调"""
        yield {
            "event": event.event_type,
            "data": json.dumps({
                "type": event.event_type,
                "round": event.round,
                "agent": event.agent,
                "content": event.content,
                "timestamp": event.timestamp.isoformat(),
            })
        }
    
    try:
        # 运行辩论
        # 注意：辩论引擎只接受 context_paths（字符串列表），analyses 是输出结果
        report = await engine.run_debate(
            topic=report.topic,
            context_paths=[],  # 暂不支持上下文，后续可传入 Obsidian 笔记路径
            rounds=report.rounds,
            emit_callback=emit_callback,
        )
        
        # 保存到 Obsidian
        try:
            file_path = obsidian_writer.save_debate(report)
            report.obsidian_path = str(file_path)
        except Exception as e:
            logger.warning(f"保存到 Obsidian 失败: {e}")
        
        _debates[debate_id] = report
        
        # 发送完成事件
        yield {
            "event": "done",
            "data": json.dumps({
                "id": debate_id,
                "status": report.status.value,
                "obsidian_path": report.obsidian_path,
            })
        }
        
    except Exception as e:
        logger.error(f"辩论执行失败: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }


@router.post("/start", response_model=DebateResponse)
async def start_debate(request: DebateStartRequest):
    """开始新辩论"""
    try:
        Config.validate()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 创建辩论报告
    report = DebateReport(
        id=str(uuid.uuid4()),
        topic=request.topic,
        participants=[AgentRole.INVESTOR, AgentRole.TECH_EXPERT, AgentRole.LEGAL],
        rounds=request.rounds,
        status=DebateStatus.PENDING,
    )
    
    # 存储
    _debates[report.id] = report
    
    return DebateResponse(
        id=report.id,
        topic=report.topic,
        status=report.status,
        progress=0.0,
        message="辩论已创建，请订阅 SSE 流获取实时进度",
    )


@router.get("/{debate_id}/stream")
async def stream_debate(debate_id: str):
    """SSE 流式获取辩论进度"""
    if debate_id not in _debates:
        raise HTTPException(status_code=404, detail="辩论不存在")
    
    report = _debates[debate_id]
    
    async def event_generator():
        engine = get_debate_engine()
        obsidian_writer = get_obsidian_writer()
        
        async def emit_callback(event: DebateStreamEvent):
            """发送事件的回调"""
            yield {
                "event": event.event_type,
                "data": json.dumps({
                    "type": event.event_type,
                    "round": event.round,
                    "agent": event.agent,
                    "content": event.content,
                    "timestamp": event.timestamp.isoformat(),
                })
            }
        
        try:
            # 运行辩论
            report = await engine.run_debate(
                topic=report.topic,
                context_paths=[],  # 暂不支持上下文
                rounds=report.rounds,
                emit_callback=emit_callback,
            )
            
            # 保存到 Obsidian
            try:
                file_path = obsidian_writer.save_debate(report)
                report.obsidian_path = str(file_path)
            except Exception as e:
                logger.warning(f"保存到 Obsidian 失败: {e}")
            
            _debates[debate_id] = report
            
            # 发送完成事件
            yield {
                "event": "done",
                "data": json.dumps({
                    "id": debate_id,
                    "status": report.status.value,
                    "obsidian_path": report.obsidian_path,
                    "final_summary": report.final_summary,
                })
            }
            
        except Exception as e:
            logger.error(f"辩论执行失败: {e}")
            _debates[debate_id].status = DebateStatus.FAILED
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


@router.get("/{debate_id}", response_model=DebateReport)
async def get_debate(debate_id: str):
    """获取辩论结果"""
    if debate_id not in _debates:
        raise HTTPException(status_code=404, detail="辩论不存在")
    return _debates[debate_id]


@router.get("/", response_model=List[DebateResponse])
async def list_debates():
    """列出所有辩论"""
    return [
        DebateResponse(
            id=id,
            topic=report.topic,
            status=report.status,
            progress=1.0 if report.status == DebateStatus.COMPLETED else 0.0,
            message=f"{report.topic} - {report.status.value}",
        )
        for id, report in _debates.items()
    ]


# Obsidian API 路由
obsidian_router = APIRouter(prefix="/api/obsidian", tags=["Obsidian"])

from ..core.config import Config


@obsidian_router.get("/notes", response_model=List[dict])
async def list_obsidian_notes(directory: str = None):
    """列出 Vault 笔记"""
    try:
        reader = get_obsidian_reader()
        notes = reader.list_notes(directory)
        return [note.to_dict() for note in notes]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@obsidian_router.get("/notes/{path:path}", response_model=dict)
async def read_obsidian_note(path: str):
    """读取笔记内容"""
    try:
        reader = get_obsidian_reader()
        file_path = reader.vault_path / path
        note = reader.read_note(file_path)
        return {
            "path": note.relative_path,
            "title": note.title,
            "tags": note.tags,
            "date": note.date,
            "content": note.content,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="笔记不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@obsidian_router.get("/search", response_model=List[dict])
async def search_obsidian_notes(q: str, directory: str = None):
    """搜索笔记"""
    try:
        reader = get_obsidian_reader()
        notes = reader.search_notes(q, directory)
        return [note.to_dict() for note in notes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))