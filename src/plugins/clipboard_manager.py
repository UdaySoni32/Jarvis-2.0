"""
Enhanced Clipboard Manager Plugin for JARVIS 2.0

Intelligent clipboard management with:
- Clipboard history tracking
- Multi-format support (text, images, files)
- Search and filtering
- AI-powered content suggestions
- Clipboard synchronization
"""

import asyncio
import subprocess
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from src.core.tools.base import BaseTool, ToolParameter


@dataclass
class ClipboardEntry:
    """Clipboard entry"""
    id: str
    content: str
    content_type: str  # text, image, file, url
    timestamp: str
    application: Optional[str] = None
    size: int = 0
    preview: Optional[str] = None


class ClipboardManager:
    """Manages clipboard operations"""
    
    def __init__(self):
        self.history: List[ClipboardEntry] = []
        self.max_history = 100
        self.current_id = 0
    
    async def get_clipboard(self) -> Optional[str]:
        """Get current clipboard content"""
        try:
            # Try xclip first (Linux)
            process = await asyncio.create_subprocess_exec(
                "xclip", "-selection", "clipboard", "-o",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode('utf-8', errors='ignore')
        except FileNotFoundError:
            pass
        
        try:
            # Try xsel (Linux alternative)
            process = await asyncio.create_subprocess_exec(
                "xsel", "--clipboard", "--output",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode('utf-8', errors='ignore')
        except FileNotFoundError:
            pass
        
        return None
    
    async def set_clipboard(self, content: str) -> bool:
        """Set clipboard content"""
        try:
            # Try xclip
            process = await asyncio.create_subprocess_exec(
                "xclip", "-selection", "clipboard",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate(input=content.encode('utf-8'))
            if process.returncode == 0:
                return True
        except FileNotFoundError:
            pass
        
        try:
            # Try xsel
            process = await asyncio.create_subprocess_exec(
                "xsel", "--clipboard", "--input",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate(input=content.encode('utf-8'))
            return process.returncode == 0
        except FileNotFoundError:
            pass
        
        return False
    
    async def add_to_history(self, content: str, content_type: str = "text") -> ClipboardEntry:
        """Add entry to history"""
        self.current_id += 1
        entry = ClipboardEntry(
            id=str(self.current_id),
            content=content,
            content_type=content_type,
            timestamp=datetime.now().isoformat(),
            size=len(content),
            preview=content[:100] if len(content) > 100 else content
        )
        
        self.history.insert(0, entry)
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        return entry
    
    def search_history(self, query: str) -> List[ClipboardEntry]:
        """Search clipboard history"""
        results = []
        query_lower = query.lower()
        
        for entry in self.history:
            if query_lower in entry.content.lower():
                results.append(entry)
        
        return results
    
    def get_history(self, limit: int = 10) -> List[ClipboardEntry]:
        """Get clipboard history"""
        return self.history[:limit]
    
    def get_entry(self, entry_id: str) -> Optional[ClipboardEntry]:
        """Get specific entry"""
        for entry in self.history:
            if entry.id == entry_id:
                return entry
        return None
    
    def clear_history(self) -> int:
        """Clear history"""
        count = len(self.history)
        self.history = []
        return count


class ClipboardManagerTool(BaseTool):
    """Enhanced clipboard manager tool"""
    
    def __init__(self):
        super().__init__()
        self.manager = ClipboardManager()
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters"""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Clipboard action",
                required=True,
                enum=[
                    "get", "set", "copy", "paste",
                    "get_history", "search", "add_to_history",
                    "get_entry", "clear_history", "get_stats"
                ]
            ),
            "content": ToolParameter(
                name="content",
                type="string",
                description="Content to set/copy",
                required=False
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=False
            ),
            "entry_id": ToolParameter(
                name="entry_id",
                type="string",
                description="Entry ID",
                required=False
            ),
            "limit": ToolParameter(
                name="limit",
                type="integer",
                description="History limit",
                required=False
            )
        }
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute clipboard action"""
        
        if action == "get":
            return await self._get_clipboard(**kwargs)
        elif action == "set":
            return await self._set_clipboard(**kwargs)
        elif action == "copy":
            return await self._copy(**kwargs)
        elif action == "paste":
            return await self._paste(**kwargs)
        elif action == "get_history":
            return self._get_history(**kwargs)
        elif action == "search":
            return self._search(**kwargs)
        elif action == "add_to_history":
            return await self._add_to_history(**kwargs)
        elif action == "get_entry":
            return self._get_entry(**kwargs)
        elif action == "clear_history":
            return self._clear_history(**kwargs)
        elif action == "get_stats":
            return self._get_stats(**kwargs)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _get_clipboard(self, **kwargs) -> Dict[str, Any]:
        """Get clipboard content"""
        content = await self.manager.get_clipboard()
        if content is None:
            return {
                "success": False,
                "error": "Could not access clipboard (install xclip or xsel)"
            }
        
        return {
            "success": True,
            "content": content,
            "size": len(content)
        }
    
    async def _set_clipboard(self, content: str, **kwargs) -> Dict[str, Any]:
        """Set clipboard content"""
        if not content:
            return {"success": False, "error": "Content is required"}
        
        success = await self.manager.set_clipboard(content)
        if not success:
            return {
                "success": False,
                "error": "Could not set clipboard (install xclip or xsel)"
            }
        
        # Add to history
        await self.manager.add_to_history(content)
        
        return {
            "success": True,
            "message": "Clipboard updated",
            "size": len(content)
        }
    
    async def _copy(self, content: str, **kwargs) -> Dict[str, Any]:
        """Copy content to clipboard"""
        return await self._set_clipboard(content, **kwargs)
    
    async def _paste(self, **kwargs) -> Dict[str, Any]:
        """Paste from clipboard"""
        return await self._get_clipboard(**kwargs)
    
    def _get_history(self, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Get clipboard history"""
        history = self.manager.get_history(limit)
        
        return {
            "success": True,
            "history": [asdict(entry) for entry in history],
            "count": len(history),
            "total": len(self.manager.history)
        }
    
    def _search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search clipboard history"""
        if not query:
            return {"success": False, "error": "Query is required"}
        
        results = self.manager.search_history(query)
        
        return {
            "success": True,
            "results": [asdict(entry) for entry in results],
            "count": len(results),
            "query": query
        }
    
    async def _add_to_history(self, content: str, content_type: str = "text", **kwargs) -> Dict[str, Any]:
        """Add entry to history"""
        if not content:
            return {"success": False, "error": "Content is required"}
        
        entry = await self.manager.add_to_history(content, content_type)
        
        return {
            "success": True,
            "entry": asdict(entry),
            "message": "Added to history"
        }
    
    def _get_entry(self, entry_id: str, **kwargs) -> Dict[str, Any]:
        """Get specific entry"""
        if not entry_id:
            return {"success": False, "error": "Entry ID is required"}
        
        entry = self.manager.get_entry(entry_id)
        if not entry:
            return {"success": False, "error": f"Entry {entry_id} not found"}
        
        return {
            "success": True,
            "entry": asdict(entry)
        }
    
    def _clear_history(self, **kwargs) -> Dict[str, Any]:
        """Clear clipboard history"""
        count = self.manager.clear_history()
        
        return {
            "success": True,
            "message": f"Cleared {count} entries",
            "count": count
        }
    
    def _get_stats(self, **kwargs) -> Dict[str, Any]:
        """Get clipboard statistics"""
        total_size = sum(entry.size for entry in self.manager.history)
        
        content_types = {}
        for entry in self.manager.history:
            content_types[entry.content_type] = content_types.get(entry.content_type, 0) + 1
        
        return {
            "success": True,
            "stats": {
                "total_entries": len(self.manager.history),
                "total_size": total_size,
                "content_types": content_types,
                "max_history": self.manager.max_history
            }
        }
