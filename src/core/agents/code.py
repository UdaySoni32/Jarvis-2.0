"""
Code Agent - Specialized in code generation, analysis, and debugging.
"""

from typing import Dict, List, Any, Optional
import re

from .base import BaseAgent, AgentStatus
from ..logger import logger


class CodeAgent(BaseAgent):
    """
    Agent specialized in code-related tasks.
    
    Capabilities:
    - Code generation
    - Code analysis and review
    - Bug detection
    - Code explanation
    - Refactoring suggestions
    """
    
    def __init__(self):
        super().__init__(
            name="CodeAgent",
            description="Generates, analyzes, and debugs code"
        )
        self.supported_languages = [
            "python", "javascript", "typescript", "java", "c++", 
            "c", "go", "rust", "ruby", "php", "swift", "kotlin"
        ]
    
    def can_handle(self, task: str) -> bool:
        """Check if task is code-related."""
        code_keywords = [
            "code", "function", "class", "debug", "fix", "error",
            "implement", "program", "script", "algorithm", "bug",
            "refactor", "optimize", "review"
        ]
        task_lower = task.lower()
        
        # Check for code keywords
        has_code_keyword = any(keyword in task_lower for keyword in code_keywords)
        
        # Check for language names
        has_language = any(lang in task_lower for lang in self.supported_languages)
        
        return has_code_keyword or has_language
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute code-related task.
        
        Args:
            task: Code task
            context: Optional context (can include existing code)
            
        Returns:
            Dictionary with code result
        """
        try:
            logger.info(f"CodeAgent: Processing '{task[:50]}...'")
            
            # Determine task type
            task_type = self._determine_task_type(task)
            
            # Get existing code from context if available
            existing_code = context.get("code", "") if context else ""
            language = context.get("language", "python") if context else "python"
            
            # Execute based on task type
            if task_type == "generate":
                result = await self._generate_code(task, language)
            elif task_type == "debug":
                result = await self._debug_code(task, existing_code, language)
            elif task_type == "explain":
                result = await self._explain_code(existing_code or task, language)
            elif task_type == "review":
                result = await self._review_code(existing_code or task, language)
            else:
                result = await self._generate_code(task, language)
            
            self.add_to_history(task, result)
            
            return {
                "success": True,
                "task_type": task_type,
                "result": result,
                "agent": self.name
            }
            
        except Exception as e:
            logger.error(f"CodeAgent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    def _determine_task_type(self, task: str) -> str:
        """Determine type of code task."""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["debug", "fix", "error", "bug"]):
            return "debug"
        elif any(word in task_lower for word in ["explain", "what does", "how does"]):
            return "explain"
        elif any(word in task_lower for word in ["review", "analyze", "check"]):
            return "review"
        else:
            return "generate"
    
    async def _generate_code(self, task: str, language: str) -> Dict[str, Any]:
        """Generate code based on requirements."""
        prompt = f"""Generate {language} code for the following task:

{task}

Provide:
1. Clean, working code
2. Comments explaining key parts
3. Example usage if applicable

Code:"""
        
        code = await self.think(prompt)
        
        # Extract actual code blocks if wrapped in markdown
        code_blocks = self._extract_code_blocks(code)
        if code_blocks:
            code = code_blocks[0]
        
        return {
            "code": code,
            "language": language,
            "type": "generated",
            "explanation": self._extract_explanation(code)
        }
    
    async def _debug_code(self, task: str, code: str, language: str) -> Dict[str, Any]:
        """Debug code and suggest fixes."""
        prompt = f"""Debug this {language} code:

{code}

Issue: {task}

Provide:
1. Problem identification
2. Fixed code
3. Explanation of the fix

Analysis:"""
        
        analysis = await self.think(prompt)
        
        # Extract fixed code
        code_blocks = self._extract_code_blocks(analysis)
        fixed_code = code_blocks[0] if code_blocks else code
        
        return {
            "original_code": code,
            "fixed_code": fixed_code,
            "analysis": analysis,
            "language": language,
            "type": "debug"
        }
    
    async def _explain_code(self, code: str, language: str) -> Dict[str, Any]:
        """Explain what code does."""
        prompt = f"""Explain this {language} code clearly:

{code}

Provide:
1. Overall purpose
2. Step-by-step breakdown
3. Key concepts used

Explanation:"""
        
        explanation = await self.think(prompt)
        
        return {
            "code": code,
            "explanation": explanation,
            "language": language,
            "type": "explanation",
            "complexity": self._estimate_complexity(code)
        }
    
    async def _review_code(self, code: str, language: str) -> Dict[str, Any]:
        """Review code quality and suggest improvements."""
        prompt = f"""Review this {language} code:

{code}

Provide:
1. Code quality assessment
2. Potential issues
3. Improvement suggestions
4. Best practices

Review:"""
        
        review = await self.think(prompt)
        
        return {
            "code": code,
            "review": review,
            "language": language,
            "type": "review",
            "issues": self._extract_issues(review)
        }
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from markdown."""
        # Match ```language\ncode\n``` or ```\ncode\n```
        pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches if matches else []
    
    def _extract_explanation(self, text: str) -> str:
        """Extract explanation text from code output."""
        lines = text.split('\n')
        explanation_lines = []
        
        for line in lines:
            # Look for comment lines
            if line.strip().startswith('#') or line.strip().startswith('//'):
                explanation_lines.append(line.strip().lstrip('#/').strip())
        
        return ' '.join(explanation_lines) if explanation_lines else "Code generated successfully"
    
    def _extract_issues(self, review_text: str) -> List[str]:
        """Extract issues from review text."""
        issues = []
        lines = review_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for issue indicators
            if any(word in line.lower() for word in ["issue", "problem", "warning", "error", "concern"]):
                if line.startswith(('-', '•', '*')) or (len(line) > 0 and line[0].isdigit()):
                    issue = line.lstrip('-•*0123456789.)').strip()
                    if issue:
                        issues.append(issue)
        
        return issues
    
    def _estimate_complexity(self, code: str) -> str:
        """Estimate code complexity (simple heuristic)."""
        lines = len([l for l in code.split('\n') if l.strip()])
        
        if lines < 10:
            return "low"
        elif lines < 50:
            return "medium"
        else:
            return "high"
    
    def get_capabilities(self) -> List[str]:
        """Get code agent capabilities."""
        return super().get_capabilities() + [
            "Code generation",
            "Bug detection and fixing",
            "Code explanation",
            "Code review",
            f"Supports {len(self.supported_languages)} languages"
        ]


# Create global instance
code_agent = CodeAgent()
