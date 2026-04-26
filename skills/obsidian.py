"""
Obsidian 技能 - 知识库管理
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import frontmatter

from .base import SkillBase, SkillConfig, RunnableSkill, SkillResult

logger = logging.getLogger(__name__)


@dataclass
class NoteInfo:
    """笔记信息"""
    path: Path
    title: str
    content: str
    frontmatter: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "title": self.title,
            "content": self.content,
            "frontmatter": self.frontmatter,
        }


class ObsidianSkill(RunnableSkill):
    """Obsidian 技能"""
    
    EXCLUDE_DIRS = {".obsidian", ".trash"}
    
    def __init__(
        self,
        vault_path: str,
        config: Optional[SkillConfig] = None
    ):
        super().__init__(config)
        self.vault_path = Path(vault_path)
        self._validated = False
    
    def _should_exclude(self, path: Path) -> bool:
        """检查是否排除"""
        parts = path.parts
        for exclude in self.EXCLUDE_DIRS:
            if exclude in parts:
                return True
        return False
    
    async def run(
        self,
        action: str,
        **kwargs
    ) -> Any:
        """执行操作"""
        if not self._validated:
            await self._validate_vault()
        
        if action == "list":
            return await self.list_notes(kwargs.get("directory"))
        elif action == "read":
            return await self.read_note(kwargs.get("path"))
        elif action == "search":
            return await self.search_notes(kwargs.get("query"))
        elif action == "write":
            return await self.write_note(
                kwargs.get("title"),
                kwargs.get("content"),
                kwargs.get("frontmatter", {}),
            )
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _validate_vault(self) -> None:
        """验证 vault"""
        if not self.vault_path.exists():
            raise ValueError(f"Vault not found: {self.vault_path}")
        self._validated = True
    
    async def list_notes(self, directory: Optional[str] = None) -> List[NoteInfo]:
        """列出笔记"""
        if directory:
            search_path = self.vault_path / directory
        else:
            search_path = self.vault_path
        
        notes = []
        for path in search_path.rglob("*.md"):
            if self._should_exclude(path):
                continue
            try:
                note = await self._read_note_file(path)
                notes.append(note)
            except Exception as e:
                logger.warning(f"Read note failed: {path} - {e}")
        
        return notes
    
    async def read_note(self, path: str) -> NoteInfo:
        """读取笔记"""
        file_path = self.vault_path / path
        return await self._read_note_file(file_path)
    
    async def _read_note_file(self, path: Path) -> NoteInfo:
        """读取笔记文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            post = frontmatter.loads(content)
            fm = dict(post.metadata)
            body = post.content
        except Exception:
            fm = {}
            body = content
        
        title = fm.get("title", path.stem)
        
        return NoteInfo(
            path=path,
            title=title,
            content=body.strip(),
            frontmatter=fm,
        )
    
    async def search_notes(self, query: str) -> List[NoteInfo]:
        """搜索笔记"""
        notes = await self.list_notes()
        query_lower = query.lower()
        
        results = []
        for note in notes:
            if query_lower in note.title.lower() or query_lower in note.content.lower():
                results.append(note)
        
        return results
    
    async def write_note(
        self,
        title: str,
        content: str,
        frontmatter: Optional[Dict[str, Any]] = None,
    ) -> NoteInfo:
        """写入笔记"""
        from datetime import datetime
        
        fm = frontmatter or {}
        fm["title"] = title
        fm["date"] = fm.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 生成文件名
        safe_title = "".join(c if c.isalnum() else "-" for c in title)[:50]
        filename = f"{safe_title}.md"
        file_path = self.vault_path / filename
        
        # 写入
        post = frontmatter.Post(content)
        post.metadata = fm
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
        
        logger.info(f"Written note: {file_path}")
        
        return NoteInfo(
            path=file_path,
            title=title,
            content=content,
            frontmatter=fm,
        )
    
    async def execute(self, action: str, **kwargs) -> SkillResult:
        """执行"""
        try:
            result = await self.run(action, **kwargs)
            
            if isinstance(result, List):
                data = [n.to_dict() for n in result]
            elif isinstance(result, NoteInfo):
                data = result.to_dict()
            else:
                data = result
            
            return SkillResult(success=True, data=data)
        except Exception as e:
            logger.error(f"Obsidian action failed: {e}")
            return SkillResult(success=False, error=str(e))


# 别名
ObsidianRunner = ObsidianSkill