from __future__ import annotations
import httpx
from .base import BaseTool, ToolResult
from src.config import OPENCORPORATES_API_KEY


class OpenCorporatesTool(BaseTool):
    name = "opencorporates"
    description = "Query OpenCorporates for company registration data"

    BASE_URL = "https://api.opencorporates.com/v0.4"

    async def run(self, params: dict) -> ToolResult:
        company_name = params.get("company_name", "")
        jurisdiction = params.get("jurisdiction", "")

        if not company_name:
            return ToolResult(success=False, error="No company name provided")

        try:
            url = f"{self.BASE_URL}/companies/search"
            query_params = {"q": company_name, "format": "json"}
            if jurisdiction:
                query_params["jurisdiction_code"] = jurisdiction
            if OPENCORPORATES_API_KEY:
                query_params["api_token"] = OPENCORPORATES_API_KEY

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=query_params)
                resp.raise_for_status()
                data = resp.json()
                companies = data.get("results", {}).get("companies", [])
                if not companies:
                    return ToolResult(
                        success=False,
                        error=f"No OpenCorporates results for '{company_name}'",
                    )
                results = []
                lines = []
                for c in companies[:10]:
                    cdata = c.get("company", {})
                    name = cdata.get("name", "")
                    jur = cdata.get("jurisdiction_code", "")
                    inc = cdata.get("incorporation_date", "")
                    status = cdata.get("current_status", "")
                    company_number = cdata.get("company_number", "")
                    oc_url = cdata.get("opencorporates_url", "")
                    results.append(cdata)
                    lines.append(f"{name} [{jur}] #{company_number} - {status} (inc: {inc})")
                    lines.append(f"  URL: {oc_url}")

                snippet = "\n".join(lines)
                return ToolResult(
                    success=True,
                    data=results,
                    source_type="opencorporates_api",
                    source_url=oc_url or url,
                    title=f"OpenCorporates: {company_name}",
                    snippet=snippet,
                    raw_text=str(data)[:10000],
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
