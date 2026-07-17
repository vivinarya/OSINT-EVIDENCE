from __future__ import annotations
import httpx
from .base import BaseTool, ToolResult
from src.config import OPENSANCTIONS_API_KEY


class OpenSanctionsTool(BaseTool):
    name = "opensanctions"
    description = "Query OpenSanctions for sanctions/PEP/watchlist data"

    BASE_URL = "https://api.opensanctions.org"

    async def run(self, params: dict) -> ToolResult:
        entity_name = params.get("entity", "")
        if not entity_name:
            return ToolResult(success=False, error="No entity name provided")

        try:
            headers = {}
            if OPENSANCTIONS_API_KEY:
                headers["Authorization"] = f"Bearer {OPENSANCTIONS_API_KEY}"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/search/default",
                    params={"q": entity_name},
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    return ToolResult(
                        success=False,
                        error=f"No sanctions results found for '{entity_name}'",
                    )

                lines = []
                for r in results[:10]:
                    name = r.get("name", "")
                    schema = r.get("schema", "")
                    topics = ", ".join(r.get("topics", []))
                    countries = ", ".join(r.get("countries", []))
                    lines.append(f"{name} ({schema}) - {topics} - {countries}")

                snippet = "\n".join(lines)
                return ToolResult(
                    success=True,
                    data=results,
                    source_type="opensanctions_api",
                    source_url=f"{self.BASE_URL}/search/default?q={entity_name}",
                    title=f"OpenSanctions: {entity_name}",
                    snippet=snippet,
                    raw_text=str(data)[:10000],
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
