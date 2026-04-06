"""Web search tool using DuckDuckGo."""

from typing import Dict, List
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from core.tools.base import BaseTool, ToolParameter


class WebSearchTool(BaseTool):
    """Searches the web using DuckDuckGo."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True,
            ),
            "max_results": ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results",
                required=False,
                default=5,
            ),
        }

    async def execute(self, query: str, max_results: int = 5) -> Dict:
        """
        Search the web.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            Search results
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx not installed. Install with: pip install httpx")

        try:
            # Use DuckDuckGo Instant Answer API
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                    },
                )
                response.raise_for_status()
                data = response.json()

            results = []

            # Get instant answer if available
            if data.get("Abstract"):
                results.append(
                    {
                        "type": "instant_answer",
                        "title": data.get("Heading", ""),
                        "text": data.get("Abstract", ""),
                        "url": data.get("AbstractURL", ""),
                        "source": data.get("AbstractSource", ""),
                    }
                )

            # Get related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append(
                        {
                            "type": "related",
                            "title": topic.get("Text", "").split(" - ")[0]
                            if " - " in topic.get("Text", "")
                            else "",
                            "text": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                        }
                    )

            # If no results, try a different approach
            if not results:
                # Try HTML scraping API
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"https://html.duckduckgo.com/html/",
                        params={"q": query},
                        follow_redirects=True,
                    )

                    if "No results" not in response.text:
                        results.append(
                            {
                                "type": "web_search",
                                "text": f"Found web results for '{query}'. Visit DuckDuckGo for full results.",
                                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                            }
                        )

            return {
                "query": query,
                "results_count": len(results),
                "results": results[:max_results],
                "search_url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            }

        except Exception as e:
            raise ValueError(f"Failed to search: {e}")
