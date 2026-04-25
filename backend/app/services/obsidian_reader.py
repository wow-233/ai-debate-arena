"""
Obsidian 读取服务 - 从 Vault 读取笔记作为辩论上下文
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import frontmatter
import logging
import re

from ..core.config import Config

logger = logging.getLogger(__name__)


class NoteInfo:
    """笔记信息"""
    def __init__(self, path: Path, title: str = "", tags: List[str] = None, 
                 date: str = "", content: str = ""):
        self.path = path
        self.title = title
        self.tags = tags or []
        self.date = date
        self.content = content
    
    @property
    def relative_path(self) -> str:
        return str(self.path)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.relative_path,
            "title": self.title,
            "tags": self.tags,
            "date": self.date,
        }


class ObsidianReader:
    """Obsidian Markdown 读取器"""
    
    # 排除的目录
    EXCLUDE_DIRS = {".obsidian", ".trash"}
    
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path or Config.get_obsidian_path())
        self.context_dir = self.vault_path / "20 - Context"
    
    def _should_exclude(self, path: Path) -> bool:
        """检查是否应排除路径"""
        parts = path.parts
        for exclude in self.EXCLUDE_DIRS:
            if exclude in parts:
                return True
        return False
    
    def list_notes(self, directory: str = None, extensions: List[str] = None) -> List[NoteInfo]:
        """列出目录下的所有笔记"""
        if directory:
            search_path = self.vault_path / directory
        else:
            search_path = self.vault_path
        
        extensions = extensions or [".md"]
        notes = []
        
        for path in search_path.rglob("*"):
            if self._should_exclude(path):
                continue
            if path.is_file() and path.suffix in extensions:
                try:
                    note = self.read_note(path)
                    notes.append(note)
                except Exception as e:
                    logger.warning(f"读取笔记失败 {path}: {e}")
        
        return sorted(notes, key=lambda n: n.date or "", reverse=True)
    
    def read_note(self, path: Path) -> NoteInfo:
        """读取单个笔记"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析 frontmatter
        try:
            post = frontmatter.loads(content)
            metadata = post.metadata
            content = post.content
        except Exception:
            metadata = {}
            content = content
        
        title = metadata.get("title", path.stem)
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        date = str(metadata.get("date", ""))
        
        return NoteInfo(
            path=path,
            title=title,
            tags=tags,
            date=date,
            content=content.strip(),
        )
    
    def read_by_paths(self, paths: List[str]) -> List[NoteInfo]:
        """根据路径列表读取笔记"""
        notes = []
        for path_str in paths:
            try:
                # 支持相对路径和绝对路径
                if Path(path_str).is_absolute():
                    path = Path(path_str)
                else:
                    path = self.vault_path / path_str
                
                if path.exists():
                    note = self.read_note(path)
                    notes.append(note)
                else:
                    logger.warning(f"笔记路径不存在: {path}")
            except Exception as e:
                logger.error(f"读取笔记失败 {path_str}: {e}")
        
        return notes
    
    def build_context(self, paths: List[str]) -> str:
        """构建辩论上下文文本"""
        notes = self.read_by_paths(paths)
        
        if not notes:
            return ""
        
        context_parts = []
        context_parts.append("# 参考资料\n")
        
        for note in notes:
            context_parts.append(f"## {note.title}\n")
            context_parts.append(note.content)
            context_parts.append(f"\n*来源: [[{note.path.stem}]]*\n")
            context_parts.append("---\n")
        
        return "\n".join(context_parts)
    
    def search_notes(self, query: str, directory: str = None) -> List[NoteInfo]:
        """搜索笔记"""
        all_notes = self.list_notes(directory)
        query_lower = query.lower()
        
        results = []
        for note in all_notes:
            # 简单关键词匹配
            if (query_lower in note.title.lower() or 
                query_lower in note.content.lower()):
                results.append(note)
        
        return results
    
    def get_hub_notes(self) -> Dict[str, NoteInfo]:
        """获取枢纽笔记"""
        hub_dir = self.vault_path / "99 - Meta" / "Hubs"
        hubs = {}
        
        if hub_dir.exists():
            for hub_file in hub_dir.glob("*.md"):
                try:
                    note = self.read_note(hub_file)
                    hubs[hub_file.stem] = note
                except Exception as e:
                    logger.warning(f"读取 Hub 笔记失败 {hub_file}: {e}")
        
        return hubs


# 全局实例
_reader: Optional[ObsidianReader] = None


def get_obsidian_reader(vault_path: str = None) -> ObsidianReader:
    """获取 Obsidian 读取器单例"""
    global _reader
    if _reader is None:
        _reader = ObsidianReader(vault_path)
    return _reader