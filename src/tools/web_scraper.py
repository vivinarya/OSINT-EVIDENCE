from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from .base import BaseTool, ToolResult


class WebScraperTool(BaseTool):
    name = "web_scraper"
    description = "Fetch and clean article/HTML content from a URL"

    async def run(self, params: dict) -> ToolResult:
        url = params.get("url", "")
        if not url:
            return ToolResult(success=False, error="No URL provided")
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36"
                })
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                title_tag = soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                snippet = text[:500].strip()
                return ToolResult(
                    success=True,
                    data={"text": text, "html": resp.text},
                    source_type="web_page",
                    source_url=url,
                    title=title,
                    snippet=snippet,
                    raw_text=text[:10000],
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e), source_url=url)
