from __future__ import annotations
import csv
import json
from pathlib import Path
from .base import BaseTool, ToolResult


SDN_PATH = Path("datasets/ofac_sdn.csv")

SDN_COLUMNS = [
    "ent_num", "sdn_name", "sdn_type", "program",
    "title", "call_sign", "vess_type", "tonnage",
    "grt", "vess_flag", "vess_owner", "remarks",
]


class OFACSDNTool(BaseTool):
    name = "ofac_sdn"
    description = "Query the OFAC Specially Designated Nationals list for sanctions entities"

    async def run(self, params: dict) -> ToolResult:
        query = (params.get("query") or "").lower()
        country = (params.get("country") or "").lower()
        program = (params.get("program") or "").lower()
        limit = params.get("limit") or 20

        if not SDN_PATH.exists():
            return ToolResult(success=False, error=f"SDN list not found at {SDN_PATH}")

        if not query and not country and not program:
            return ToolResult(success=False, error="Provide at least one of: query, country, program")

        results = []
        with open(SDN_PATH, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 4:
                    continue
                name = (row[1] or "").lower() if len(row) > 1 else ""
                row_country = (row[3] or "").lower() if len(row) > 3 else ""
                row_program = (row[3] or "").lower() if len(row) > 3 else ""

                matches = True
                if query and query not in name:
                    matches = False
                if country and country not in row_country:
                    matches = False
                if program and program not in row_program:
                    matches = False

                if matches:
                    entry = {SDN_COLUMNS[i]: (row[i] if i < len(row) else "") for i in range(len(SDN_COLUMNS))}
                    results.append(entry)
                    if len(results) >= limit:
                        break

        if not results:
            return ToolResult(success=False, error=f"No SDN entries matching query")

        lines = [f"Found {len(results)} SDN entries:"]
        for r in results:
            name = r.get("sdn_name", "")
            typ = r.get("sdn_type", "")
            prog = r.get("program", "")
            remarks = r.get("remarks", "")
            line = f"  {name} ({typ}) [{prog}]"
            if remarks:
                line += f" - {remarks[:80]}"
            lines.append(line)

        return ToolResult(
            success=True,
            data=results,
            source_type="ofac_sdn_list",
            source_url="https://sanctionslist.ofac.treas.gov/sdn.csv",
            title=f"OFAC SDN search: {query or country or program}",
            snippet="\n".join(lines),
            raw_text=json.dumps(results, indent=2),
        )
