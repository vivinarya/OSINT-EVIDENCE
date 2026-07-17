from __future__ import annotations
import httpx
from datetime import datetime
from .base import BaseTool, ToolResult


class WaybackTool(BaseTool):
    name = "wayback"
    description = "Check if a URL existed at a given time via the Wayback Machine"

    BASE_URL = "https://archive.org/wayback/available"

    async def run(self, params: dict) -> ToolResult:
        url = params.get("url", "")
        timestamp = params.get("timestamp", datetime.now().strftime("%Y%m%d"))

        if not url:
            return ToolResult(success=False, error="No URL provided")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    self.BASE_URL,
                    params={"url": url, "timestamp": timestamp},
                )
                resp.raise_for_status()
                data = resp.json()
                archived_snapshots = data.get("archived_snapshots", {})
                closest = archived_snapshots.get("closest", {})

                if closest and closest.get("available", False):
                    archive_url = closest.get("url", "")
                    status = closest.get("status", "200")
                    return ToolResult(
                        success=True,
                        data=closest,
                        source_type="wayback_api",
                        source_url=archive_url,
                        title=f"Wayback: {url}",
                        snippet=f"Archived at {archive_url} (status: {status})",
                        raw_text=str(data)[:5000],
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=f"No archive found for {url} at {timestamp}",
                        source_type="wayback_api",
                        source_url=url,
                        snippet="No archived version found",
                        raw_text=str(data)[:5000],
                    )
        except Exception as e:
            return ToolResult(success=False, error=str(e), source_url=url)
