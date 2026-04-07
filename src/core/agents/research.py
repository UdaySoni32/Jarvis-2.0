"""
Research Agent - Gathers and synthesizes information from multiple sources.
"""

from typing import Dict, List, Any, Optional

from .base import BaseAgent, AgentStatus
from ..logger import logger


class ResearchAgent(BaseAgent):
    """
    Agent specialized in information research and synthesis.
    
    Capabilities:
    - Web search and information gathering
    - Source summarization
    - Fact extraction
    - Multi-source synthesis
    """
    
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            description="Researches topics and synthesizes information from multiple sources"
        )
        self.sources_used: List[str] = []
    
    def can_handle(self, task: str) -> bool:
        """Check if task requires research."""
        research_keywords = [
            "research", "find", "search", "look up", "information about",
            "tell me about", "what is", "who is", "explain", "learn"
        ]
        task_lower = task.lower()
        return any(keyword in task_lower for keyword in research_keywords)
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Research the given topic.
        
        Args:
            task: Research task
            context: Optional context
            
        Returns:
            Dictionary with research results
        """
        try:
            logger.info(f"ResearchAgent: Researching '{task[:50]}...'")
            
            # Extract the topic from the task
            topic = self._extract_topic(task)
            
            # Use web search tool if available
            search_results = await self._search_web(topic)
            
            # Synthesize findings
            synthesis = await self._synthesize_findings(topic, search_results)
            
            self.add_to_history(task, synthesis)
            
            return {
                "success": True,
                "topic": topic,
                "findings": synthesis,
                "sources_count": len(self.sources_used),
                "agent": self.name
            }
            
        except Exception as e:
            logger.error(f"ResearchAgent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    def _extract_topic(self, task: str) -> str:
        """Extract main topic from task."""
        # Remove common research phrases
        topic = task.lower()
        for phrase in ["research", "find information about", "tell me about", 
                      "what is", "who is", "search for", "look up"]:
            topic = topic.replace(phrase, "")
        return topic.strip()
    
    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        results = []
        
        # Try to use websearch tool
        search_result = await self.use_tool("websearch", query=query)
        
        if search_result.get("success"):
            # Parse search results
            results_text = search_result.get("results", "")
            if results_text:
                # Simple parsing - in production would be more sophisticated
                results.append({
                    "source": "web_search",
                    "content": results_text,
                    "type": "search_results"
                })
                self.sources_used.append("Web Search")
        
        return results
    
    async def _synthesize_findings(
        self, 
        topic: str, 
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize findings from multiple sources.
        
        Args:
            topic: Research topic
            search_results: Raw search results
            
        Returns:
            Synthesized findings
        """
        if not search_results:
            # If no search results, use LLM knowledge
            synthesis_prompt = f"""Provide a comprehensive overview of: {topic}

Include:
1. Definition/Overview
2. Key points
3. Important facts
4. Relevant context

Overview:"""
            
            overview = await self.think(synthesis_prompt)
            
            return {
                "overview": overview,
                "key_points": self._extract_key_points(overview),
                "sources": ["LLM Knowledge Base"],
                "confidence": "medium"
            }
        
        # Synthesize from search results
        results_text = "\n\n".join([r["content"] for r in search_results])
        
        synthesis_prompt = f"""Based on the following search results about '{topic}', create a clear summary:

{results_text[:2000]}  # Limit to avoid token limits

Provide:
1. Main findings
2. Key points
3. Important details

Summary:"""
        
        summary = await self.think(synthesis_prompt)
        
        return {
            "overview": summary,
            "key_points": self._extract_key_points(summary),
            "sources": self.sources_used,
            "confidence": "high" if search_results else "low"
        }
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text."""
        points = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if line.startswith(('-', '•', '*')) or (len(line) > 0 and line[0].isdigit()):
                # Clean up the point
                point = line.lstrip('-•*0123456789.)').strip()
                if point:
                    points.append(point)
        
        # If no structured points found, take first few sentences
        if not points:
            sentences = text.split('.')
            points = [s.strip() + '.' for s in sentences[:3] if s.strip()]
        
        return points[:5]  # Return top 5 points
    
    def get_capabilities(self) -> List[str]:
        """Get research agent capabilities."""
        return super().get_capabilities() + [
            "Web search and information gathering",
            "Multi-source synthesis",
            "Fact extraction",
            "Source evaluation"
        ]


# Create global instance
research_agent = ResearchAgent()
