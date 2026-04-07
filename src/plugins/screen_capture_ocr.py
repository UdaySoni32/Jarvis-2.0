"""Screen Capture and OCR Plugin"""

import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import json

from src.core.tools.base import BaseTool, ToolParameter


@dataclass
class ScreenCapture:
    """Screen capture data"""
    filename: str
    path: str
    timestamp: str
    region: Optional[Tuple[int, int, int, int]] = None
    window_id: Optional[str] = None


@dataclass
class OCRResult:
    """OCR extraction result"""
    text: str
    confidence: float
    language: str
    source_image: str
    word_count: int


class ScreenCaptureManager:
    """Screen capture manager"""
    
    def __init__(self, output_dir: str = "~/Pictures/Screenshots"):
        self.output_dir = Path(output_dir).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.capture_history: List[ScreenCapture] = []
    
    async def capture_full_screen(self) -> ScreenCapture:
        """Capture full screen"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = self.output_dir / filename
        
        # Use scrot for screen capture (common on Linux)
        try:
            process = await asyncio.create_subprocess_exec(
                "scrot", str(filepath),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            capture = ScreenCapture(
                filename=filename,
                path=str(filepath),
                timestamp=timestamp
            )
            self.capture_history.append(capture)
            return capture
            
        except FileNotFoundError:
            raise RuntimeError("scrot not installed. Install with: sudo pacman -S scrot")
    
    async def capture_region(self, x: int, y: int, width: int, height: int) -> ScreenCapture:
        """Capture screen region"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_region_{timestamp}.png"
        filepath = self.output_dir / filename
        
        # Use scrot with region selection
        geometry = f"{width}x{height}+{x}+{y}"
        
        try:
            process = await asyncio.create_subprocess_exec(
                "scrot", "-a", geometry, str(filepath),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            capture = ScreenCapture(
                filename=filename,
                path=str(filepath),
                timestamp=timestamp,
                region=(x, y, width, height)
            )
            self.capture_history.append(capture)
            return capture
            
        except FileNotFoundError:
            raise RuntimeError("scrot not installed")
    
    async def capture_window(self, window_id: Optional[str] = None) -> ScreenCapture:
        """Capture active window"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_window_{timestamp}.png"
        filepath = self.output_dir / filename
        
        try:
            if window_id:
                # Capture specific window
                process = await asyncio.create_subprocess_exec(
                    "scrot", "-u", "-b", str(filepath),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Capture focused window
                process = await asyncio.create_subprocess_exec(
                    "scrot", "-u", str(filepath),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            await process.communicate()
            
            capture = ScreenCapture(
                filename=filename,
                path=str(filepath),
                timestamp=timestamp,
                window_id=window_id
            )
            self.capture_history.append(capture)
            return capture
            
        except FileNotFoundError:
            raise RuntimeError("scrot not installed")


class OCREngine:
    """OCR engine using Tesseract"""
    
    def __init__(self):
        self.default_language = "eng"
    
    async def extract_text(self, image_path: str, language: str = "eng") -> OCRResult:
        """Extract text from image"""
        try:
            # Run tesseract OCR
            process = await asyncio.create_subprocess_exec(
                "tesseract", image_path, "stdout",
                "-l", language,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Tesseract failed: {stderr.decode()}")
            
            text = stdout.decode().strip()
            
            # Count words
            word_count = len(text.split())
            
            # Simple confidence (would need --psm 6 tsv for real confidence)
            confidence = 0.85 if word_count > 0 else 0.0
            
            return OCRResult(
                text=text,
                confidence=confidence,
                language=language,
                source_image=image_path,
                word_count=word_count
            )
            
        except FileNotFoundError:
            raise RuntimeError("tesseract not installed. Install with: sudo pacman -S tesseract")
    
    async def extract_with_boxes(self, image_path: str, language: str = "eng") -> Dict:
        """Extract text with bounding boxes"""
        try:
            # Run tesseract with TSV output for word positions
            process = await asyncio.create_subprocess_exec(
                "tesseract", image_path, "stdout",
                "-l", language,
                "--psm", "6",
                "tsv",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Tesseract failed: {stderr.decode()}")
            
            lines = stdout.decode().strip().split('\n')
            
            # Parse TSV output
            words = []
            for line in lines[1:]:  # Skip header
                parts = line.split('\t')
                if len(parts) >= 12:
                    word_text = parts[11]
                    if word_text.strip():
                        words.append({
                            "text": word_text,
                            "confidence": float(parts[10]) if parts[10] != '-1' else 0,
                            "bbox": {
                                "x": int(parts[6]),
                                "y": int(parts[7]),
                                "width": int(parts[8]),
                                "height": int(parts[9])
                            }
                        })
            
            return {
                "words": words,
                "total_words": len(words),
                "source_image": image_path,
                "language": language
            }
            
        except FileNotFoundError:
            raise RuntimeError("tesseract not installed")


class ScreenCaptureOCRTool(BaseTool):
    """Screen capture and OCR tool"""
    
    def __init__(self):
        super().__init__()
        self.capture_manager = ScreenCaptureManager()
        self.ocr_engine = OCREngine()
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Action to perform",
                required=True
            ),
            "x": ToolParameter(
                name="x",
                type="integer",
                description="X coordinate for region capture",
                required=False
            ),
            "y": ToolParameter(
                name="y",
                type="integer",
                description="Y coordinate for region capture",
                required=False
            ),
            "width": ToolParameter(
                name="width",
                type="integer",
                description="Width for region capture",
                required=False
            ),
            "height": ToolParameter(
                name="height",
                type="integer",
                description="Height for region capture",
                required=False
            ),
            "image_path": ToolParameter(
                name="image_path",
                type="string",
                description="Path to image for OCR",
                required=False
            ),
            "language": ToolParameter(
                name="language",
                type="string",
                description="OCR language (default: eng)",
                required=False
            ),
            "window_id": ToolParameter(
                name="window_id",
                type="string",
                description="Window ID for window capture",
                required=False
            )
        }
    
    async def execute(self, action: str, **kwargs) -> Dict:
        """Execute screen capture or OCR action"""
        
        if action == "capture_screen":
            return await self._capture_full_screen()
        
        elif action == "capture_region":
            x = kwargs.get("x", 0)
            y = kwargs.get("y", 0)
            width = kwargs.get("width", 100)
            height = kwargs.get("height", 100)
            return await self._capture_region(x, y, width, height)
        
        elif action == "capture_window":
            window_id = kwargs.get("window_id")
            return await self._capture_window(window_id)
        
        elif action == "extract_text":
            image_path = kwargs.get("image_path")
            language = kwargs.get("language", "eng")
            return await self._extract_text(image_path, language)
        
        elif action == "extract_with_boxes":
            image_path = kwargs.get("image_path")
            language = kwargs.get("language", "eng")
            return await self._extract_with_boxes(image_path, language)
        
        elif action == "get_history":
            return self._get_capture_history()
        
        elif action == "clear_history":
            return self._clear_history()
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
    
    async def _capture_full_screen(self) -> Dict:
        """Capture full screen"""
        try:
            capture = await self.capture_manager.capture_full_screen()
            return {
                "success": True,
                "capture": {
                    "filename": capture.filename,
                    "path": capture.path,
                    "timestamp": capture.timestamp
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _capture_region(self, x: int, y: int, width: int, height: int) -> Dict:
        """Capture screen region"""
        try:
            capture = await self.capture_manager.capture_region(x, y, width, height)
            return {
                "success": True,
                "capture": {
                    "filename": capture.filename,
                    "path": capture.path,
                    "timestamp": capture.timestamp,
                    "region": capture.region
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _capture_window(self, window_id: Optional[str]) -> Dict:
        """Capture window"""
        try:
            capture = await self.capture_manager.capture_window(window_id)
            return {
                "success": True,
                "capture": {
                    "filename": capture.filename,
                    "path": capture.path,
                    "timestamp": capture.timestamp,
                    "window_id": capture.window_id
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _extract_text(self, image_path: str, language: str) -> Dict:
        """Extract text from image"""
        try:
            result = await self.ocr_engine.extract_text(image_path, language)
            return {
                "success": True,
                "ocr": {
                    "text": result.text,
                    "confidence": result.confidence,
                    "language": result.language,
                    "word_count": result.word_count,
                    "source_image": result.source_image
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _extract_with_boxes(self, image_path: str, language: str) -> Dict:
        """Extract text with bounding boxes"""
        try:
            result = await self.ocr_engine.extract_with_boxes(image_path, language)
            return {
                "success": True,
                "ocr_boxes": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_capture_history(self) -> Dict:
        """Get capture history"""
        return {
            "success": True,
            "history": [
                {
                    "filename": c.filename,
                    "path": c.path,
                    "timestamp": c.timestamp,
                    "region": c.region,
                    "window_id": c.window_id
                }
                for c in self.capture_manager.capture_history
            ],
            "count": len(self.capture_manager.capture_history)
        }
    
    def _clear_history(self) -> Dict:
        """Clear capture history"""
        count = len(self.capture_manager.capture_history)
        self.capture_manager.capture_history.clear()
        return {
            "success": True,
            "cleared": count
        }
