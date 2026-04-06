"""File operations tool."""

import os
from pathlib import Path
from typing import Dict, List

from core.tools.base import BaseTool, ToolParameter


class FileReadTool(BaseTool):
    """Reads content from a file."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "file_path": ToolParameter(
                name="file_path",
                type="string",
                description="Path to file to read",
                required=True,
            ),
            "max_lines": ToolParameter(
                name="max_lines",
                type="number",
                description="Maximum number of lines to read",
                required=False,
                default=100,
            ),
        }

    async def execute(self, file_path: str, max_lines: int = 100) -> Dict[str, any]:
        """
        Read file content.

        Args:
            file_path: Path to file
            max_lines: Maximum lines to read

        Returns:
            File content
        """
        try:
            path = Path(file_path).expanduser()

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not path.is_file():
                raise ValueError(f"Not a file: {file_path}")

            # Read file
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            total_lines = len(lines)
            truncated = total_lines > max_lines

            if truncated:
                lines = lines[:max_lines]

            return {
                "file_path": str(path),
                "content": "".join(lines),
                "total_lines": total_lines,
                "lines_returned": len(lines),
                "truncated": truncated,
            }

        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")


class FileListTool(BaseTool):
    """Lists files in a directory."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "directory": ToolParameter(
                name="directory",
                type="string",
                description="Directory path to list",
                required=True,
            ),
            "pattern": ToolParameter(
                name="pattern",
                type="string",
                description="File pattern to match (e.g., '*.py')",
                required=False,
                default="*",
            ),
        }

    async def execute(self, directory: str, pattern: str = "*") -> Dict[str, any]:
        """
        List files in directory.

        Args:
            directory: Directory path
            pattern: File pattern

        Returns:
            List of files
        """
        try:
            path = Path(directory).expanduser()

            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {directory}")

            if not path.is_dir():
                raise ValueError(f"Not a directory: {directory}")

            # List files matching pattern
            files = []
            for item in path.glob(pattern):
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "is_file": item.is_file(),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                })

            return {
                "directory": str(path),
                "pattern": pattern,
                "count": len(files),
                "files": files,
            }

        except Exception as e:
            raise ValueError(f"Failed to list directory: {e}")
