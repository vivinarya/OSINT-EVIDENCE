from __future__ import annotations
import csv
import json
from pathlib import Path
from .base import BaseTool, ToolResult


ICIJ_DIR = Path("datasets/icij")


class ICIJDataTool(BaseTool):
    name = "icij_data"
    description = "Query local ICIJ Offshore Leaks data (entities, officers, intermediaries, addresses, relationships)"

    async def run(self, params: dict) -> ToolResult:
        query_type = params.get("query_type", "search_entity")
        entity_name = params.get("entity", "").lower()
        limit = params.get("limit", 20)

        if not ICIJ_DIR.exists():
            return ToolResult(success=False, error=f"ICIJ data directory not found at {ICIJ_DIR}")

        try:
            if query_type == "search_entity":
                return self._search_entities(entity_name, limit)
            elif query_type == "search_officer":
                return self._search_officers(entity_name, limit)
            elif query_type == "search_intermediary":
                return self._search_intermediaries(entity_name, limit)
            elif query_type == "get_entity_relationships":
                return self._get_relationships(entity_name, limit)
            else:
                return ToolResult(success=False, error=f"Unknown query_type: {query_type}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _search_entities(self, name: str, limit: int) -> ToolResult:
        path = ICIJ_DIR / "nodes-entities.csv"
        if not path.exists():
            return ToolResult(success=False, error="entities CSV not found")

        results = []
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_name = (row.get("name", "") or "").lower()
                if name in row_name:
                    results.append({
                        "id": row.get("node_id", ""),
                        "name": row.get("name", ""),
                        "jurisdiction": row.get("jurisdiction", ""),
                        "jurisdiction_description": row.get("jurisdiction_description", ""),
                        "country_codes": row.get("country_codes", ""),
                        "incorporation_date": row.get("incorporation_date", ""),
                        "struck_off_date": row.get("struck_off_date", ""),
                        "company_type": row.get("company_type", ""),
                        "status": row.get("status", ""),
                        "sourceID": row.get("sourceID", ""),
                    })
                    if len(results) >= limit:
                        break

        if not results:
            return ToolResult(success=False, error=f"No entities found matching '{name}'")

        lines = [f"Found {len(results)} entities matching '{name}':"]
        for r in results:
            lines.append(f"  [{r['id']}] {r['name']} ({r['jurisdiction']}) - {r['company_type']}")
        return ToolResult(
            success=True,
            data=results,
            source_type="icij_offshore_leaks",
            source_url="https://offshoreleaks.icij.org/",
            title=f"ICIJ Entities: {name}",
            snippet="\n".join(lines),
            raw_text=json.dumps(results, indent=2),
        )

    def _search_officers(self, name: str, limit: int) -> ToolResult:
        path = ICIJ_DIR / "nodes-officers.csv"
        if not path.exists():
            return ToolResult(success=False, error="officers CSV not found")

        results = []
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_name = (row.get("name", "") or "").lower()
                if name in row_name:
                    results.append({
                        "id": row.get("node_id", ""),
                        "name": row.get("name", ""),
                        "country_codes": row.get("country_codes", ""),
                        "status": row.get("status", ""),
                        "sourceID": row.get("sourceID", ""),
                    })
                    if len(results) >= limit:
                        break

        if not results:
            return ToolResult(success=False, error=f"No officers found matching '{name}'")

        lines = [f"Found {len(results)} officers matching '{name}':"]
        for r in results:
            lines.append(f"  [{r['id']}] {r['name']} ({r.get('country_codes', '')})")
        return ToolResult(
            success=True,
            data=results,
            source_type="icij_offshore_leaks",
            source_url="https://offshoreleaks.icij.org/",
            title=f"ICIJ Officers: {name}",
            snippet="\n".join(lines),
            raw_text=json.dumps(results, indent=2),
        )

    def _search_intermediaries(self, name: str, limit: int) -> ToolResult:
        path = ICIJ_DIR / "nodes-intermediaries.csv"
        if not path.exists():
            return ToolResult(success=False, error="intermediaries CSV not found")

        results = []
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_name = (row.get("name", "") or "").lower()
                if name in row_name:
                    results.append({
                        "id": row.get("node_id", ""),
                        "name": row.get("name", ""),
                        "country_codes": row.get("country_codes", ""),
                        "status": row.get("status", ""),
                        "sourceID": row.get("sourceID", ""),
                    })
                    if len(results) >= limit:
                        break

        if not results:
            return ToolResult(success=False, error=f"No intermediaries found matching '{name}'")
        lines = [f"Found {len(results)} intermediaries matching '{name}':"]
        for r in results:
            lines.append(f"  [{r['id']}] {r['name']} ({r.get('country_codes', '')})")
        return ToolResult(
            success=True,
            data=results,
            source_type="icij_offshore_leaks",
            source_url="https://offshoreleaks.icij.org/",
            title=f"ICIJ Intermediaries: {name}",
            snippet="\n".join(lines),
            raw_text=json.dumps(results, indent=2),
        )

    def _get_relationships(self, node_id: str, limit: int) -> ToolResult:
        path = ICIJ_DIR / "relationships.csv"
        if not path.exists():
            return ToolResult(success=False, error="relationships CSV not found")

        results = []
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("node_1", "") == node_id or row.get("node_2", "") == node_id:
                    results.append({
                        "rel_type": row.get("rel_type", ""),
                        "node_1": row.get("node_1", ""),
                        "node_2": row.get("node_2", ""),
                        "sourceID": row.get("sourceID", ""),
                        "start_date": row.get("start_date", ""),
                        "end_date": row.get("end_date", ""),
                    })
                    if len(results) >= limit:
                        break

        if not results:
            return ToolResult(success=False, error=f"No relationships found for node '{node_id}'")
        lines = [f"Found {len(results)} relationships for node '{node_id}':"]
        for r in results:
            lines.append(f"  {r['node_1']} --{r['rel_type']}--> {r['node_2']}")
        return ToolResult(
            success=True,
            data=results,
            source_type="icij_offshore_leaks",
            source_url="https://offshoreleaks.icij.org/",
            title=f"ICIJ Relationships: {node_id}",
            snippet="\n".join(lines),
            raw_text=json.dumps(results, indent=2),
        )
