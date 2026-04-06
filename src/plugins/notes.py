"""Notes management tool."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import uuid

from core.tools.base import BaseTool, ToolParameter
from core.config import settings


class NotesManager:
    """Manages user notes."""

    def __init__(self):
        self.notes_dir = settings.user_data_dir / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.notes_dir / "notes.json"
        self.notes = self._load_notes()

    def _load_notes(self) -> List[Dict]:
        """Load notes from file."""
        if self.notes_file.exists():
            with open(self.notes_file, "r") as f:
                return json.load(f)
        return []

    def _save_notes(self):
        """Save notes to file."""
        with open(self.notes_file, "w") as f:
            json.dump(self.notes, f, indent=2)

    def create_note(self, title: str, content: str, tags: List[str] = None) -> Dict:
        """Create a new note."""
        note = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "content": content,
            "tags": tags or [],
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }
        self.notes.append(note)
        self._save_notes()
        return note

    def get_note(self, note_id: str) -> Dict:
        """Get a note by ID."""
        for note in self.notes:
            if note["id"] == note_id:
                return note
        return None

    def list_notes(self, tag: str = None, search: str = None) -> List[Dict]:
        """List notes, optionally filtered by tag or search."""
        filtered = self.notes

        if tag:
            filtered = [n for n in filtered if tag in n.get("tags", [])]

        if search:
            search_lower = search.lower()
            filtered = [
                n
                for n in filtered
                if search_lower in n["title"].lower()
                or search_lower in n["content"].lower()
            ]

        return filtered

    def update_note(
        self, note_id: str, title: str = None, content: str = None, tags: List[str] = None
    ) -> Dict:
        """Update a note."""
        note = self.get_note(note_id)
        if not note:
            raise ValueError(f"Note not found: {note_id}")

        if title:
            note["title"] = title
        if content:
            note["content"] = content
        if tags is not None:
            note["tags"] = tags

        note["updated"] = datetime.now().isoformat()
        self._save_notes()
        return note

    def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        for i, note in enumerate(self.notes):
            if note["id"] == note_id:
                del self.notes[i]
                self._save_notes()
                return True
        return False


# Global notes manager
notes_manager = NotesManager()


class NotesTool(BaseTool):
    """Creates and manages notes."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Notes action",
                required=True,
                enum=["create", "read", "list", "update", "delete", "search"],
            ),
            "title": ToolParameter(
                name="title",
                type="string",
                description="Note title (for create/update)",
                required=False,
            ),
            "content": ToolParameter(
                name="content",
                type="string",
                description="Note content (for create/update)",
                required=False,
            ),
            "note_id": ToolParameter(
                name="note_id",
                type="string",
                description="Note ID (for read/update/delete)",
                required=False,
            ),
            "tags": ToolParameter(
                name="tags",
                type="string",
                description="Comma-separated tags (for create/update/list)",
                required=False,
            ),
            "search": ToolParameter(
                name="search",
                type="string",
                description="Search query (for list/search)",
                required=False,
            ),
        }

    async def execute(
        self,
        action: str,
        title: str = None,
        content: str = None,
        note_id: str = None,
        tags: str = None,
        search: str = None,
    ) -> Dict:
        """
        Manage notes.

        Args:
            action: create, read, list, update, delete, or search
            title: Note title
            content: Note content
            note_id: Note ID
            tags: Tags (comma-separated)
            search: Search query

        Returns:
            Note information
        """
        tags_list = [t.strip() for t in tags.split(",")] if tags else []

        if action == "create":
            if not title or not content:
                raise ValueError("Title and content required for create")

            note = notes_manager.create_note(title, content, tags_list)
            return {
                "action": "created",
                "note": note,
                "message": f"Created note '{title}' (ID: {note['id']})",
            }

        elif action == "read":
            if not note_id:
                raise ValueError("Note ID required for read")

            note = notes_manager.get_note(note_id)
            if not note:
                raise ValueError(f"Note not found: {note_id}")

            return {"action": "read", "note": note}

        elif action in ["list", "search"]:
            notes = notes_manager.list_notes(
                tag=tags_list[0] if tags_list else None, search=search
            )

            return {
                "action": action,
                "notes": [
                    {
                        "id": n["id"],
                        "title": n["title"],
                        "tags": n["tags"],
                        "created": n["created"],
                        "preview": n["content"][:100] + "..."
                        if len(n["content"]) > 100
                        else n["content"],
                    }
                    for n in notes
                ],
                "count": len(notes),
            }

        elif action == "update":
            if not note_id:
                raise ValueError("Note ID required for update")

            note = notes_manager.update_note(note_id, title, content, tags_list)
            return {
                "action": "updated",
                "note": note,
                "message": f"Updated note {note_id}",
            }

        elif action == "delete":
            if not note_id:
                raise ValueError("Note ID required for delete")

            success = notes_manager.delete_note(note_id)
            if not success:
                raise ValueError(f"Note not found: {note_id}")

            return {
                "action": "deleted",
                "note_id": note_id,
                "message": f"Deleted note {note_id}",
            }

        else:
            raise ValueError(f"Unknown action: {action}")
