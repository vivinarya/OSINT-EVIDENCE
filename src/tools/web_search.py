from __future__ import annotations
import json
import httpx
from .base import BaseTool, ToolResult
from src.config import TAVILY_API_KEY, SERPER_API_KEY, FIRECRAWL_API_KEY
from .firecrawl_scraper import FirecrawlSearchTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for recent information on a topic"

    async def run(self, params: dict) -> ToolResult:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        if not query:
            return ToolResult(success=False, error="No query provided")

        if TAVILY_API_KEY:
            return await self._tavily_search(query, max_results)
        elif SERPER_API_KEY:
            return await self._serper_search(query, max_results)
        elif FIRECRAWL_API_KEY:
            return await FirecrawlSearchTool().run({"query": query})
        else:
            return ToolResult(success=False, error="No search API key configured. "
                                                    "Use wikidata, icij_data, ofac_sdn, or gdelt for offline queries.")

    async def _tavily_search(self, query: str, max_results: int) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": TAVILY_API_KEY, "query": query, "max_results": max_results},
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                urls = [r.get("url", "") for r in results]
                snippets = "\n".join(
                    f"- {r.get('title', '')}: {r.get('content', '')[:500]}"
                    for r in results
                )
                return ToolResult(
                    success=True,
                    data=results,
                    source_type="web_search",
                    source_url=urls[0] if urls else "",
                    title=f"Web search: {query}",
                    snippet=snippets,
                    raw_text=json.dumps(data, indent=2),
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _serper_search(self, query: str, max_results: int) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    json={"q": query, "num": max_results},
                    headers={"X-API-KEY": SERPER_API_KEY},
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("organic", [])
                snippets = "\n".join(
                    f"- {r.get('title', '')}: {r.get('snippet', '')[:500]}"
                    for r in results
                )
                return ToolResult(
                    success=True,
                    data=results,
                    source_type="web_search",
                    source_url=data.get("organic", [{}])[0].get("link", ""),
                    title=f"Web search: {query}",
                    snippet=snippets,
                    raw_text=json.dumps(data, indent=2),
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
