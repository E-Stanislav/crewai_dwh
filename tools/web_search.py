"""Tool for web search using DuckDuckGo."""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS


class WebSearchInput(BaseModel):
    """Input schema for web search."""
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=5, description="Maximum number of results")


class WebSearchTool(BaseTool):
    """Tool to search the web for information."""
    
    name: str = "web_search"
    description: str = (
        "Search the web for information. "
        "Use this to find documentation, best practices, SQL syntax help, "
        "dbt documentation, and answers to technical questions. "
        "Returns titles, URLs, and snippets from search results."
    )
    args_schema: type[BaseModel] = WebSearchInput
    
    def _run(self, query: str, max_results: int = 5) -> str:
        """Execute web search."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return f"No results found for: {query}"
            
            # Format results
            result_lines = [
                f"## Web Search Results",
                f"**Query:** {query}",
                f"**Results:** {len(results)}",
                ""
            ]
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("href", result.get("link", ""))
                snippet = result.get("body", result.get("snippet", ""))
                
                result_lines.append(f"### {i}. {title}")
                result_lines.append(f"**URL:** {url}")
                result_lines.append(f"{snippet}")
                result_lines.append("")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"Error performing web search: {str(e)}"
