from __future__ import annotations
import httpx
from .base import BaseTool, ToolResult


class WikidataTool(BaseTool):
    name = "wikidata"
    description = "Query Wikidata for structured entity data (people, orgs, relationships)"

    WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
    ENTITY_DATA = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

    async def run(self, params: dict) -> ToolResult:
        entity_name = params.get("entity", "")
        query_type = params.get("query_type", "describe")

        if not entity_name:
            return ToolResult(success=False, error="No entity name provided")

        try:
            if query_type == "describe":
                return await self._describe_entity(entity_name)
            elif query_type == "corporate":
                return await self._corporate_query(entity_name)
            elif query_type == "search":
                return await self._search_entity(entity_name)
            else:
                return ToolResult(success=False, error=f"Unknown query type: {query_type}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _sparql_query(self, query: str) -> list:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                self.WIKIDATA_SPARQL,
                params={"format": "json", "query": query},
                headers={"User-Agent": "OSINTInvestigativeAgent/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", {}).get("bindings", [])

    async def _entity_data(self, entity_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                self.ENTITY_DATA.format(entity_id),
                headers={"User-Agent": "OSINTInvestigativeAgent/1.0"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            entity = data.get("entities", {}).get(entity_id, {})
            return entity

    async def _mwapi_search(self, name: str) -> list:
        query = f"""
        SELECT ?item ?itemLabel ?itemDescription WHERE {{
          SERVICE wikibase:mwapi {{
            bd:serviceParam wikibase:api "EntitySearch".
            bd:serviceParam wikibase:endpoint "www.wikidata.org".
            bd:serviceParam mwapi:search "{name}".
            bd:serviceParam mwapi:language "en".
            ?item wikibase:apiOutputItem mwapi:item.
            ?num wikibase:apiOrdinal true.
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 5
        """
        return await self._sparql_query(query)

    async def _find_entity_id(self, name: str) -> str | None:
        bindings = await self._mwapi_search(name)
        if bindings:
            uri = bindings[0].get("item", {}).get("value", "")
            return uri.split("/")[-1] if uri else None

        query = f"""
        SELECT ?item WHERE {{
          ?item ?label "{name}"@en.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT 5
        """
        bindings = await self._sparql_query(query)
        if bindings:
            uri = bindings[0].get("item", {}).get("value", "")
            return uri.split("/")[-1] if uri else None
        return None

    async def _search_entity(self, name: str) -> ToolResult:
        bindings = await self._mwapi_search(name)
        if not bindings:
            return ToolResult(success=False, error=f"No Wikidata entity found for '{name}'")

        results = []
        for b in bindings:
            uri = b.get("item", {}).get("value", "")
            eid = uri.split("/")[-1] if uri else ""
            label = b.get("itemLabel", {}).get("value", "")
            desc = b.get("itemDescription", {}).get("value", "")
            results.append({"id": eid, "label": label, "description": desc})

        top = results[0]
        return ToolResult(
            success=True,
            data=results,
            source_type="wikidata_api",
            source_url=f"https://www.wikidata.org/wiki/{top['id']}",
            title=top["label"],
            snippet=f"Wikidata: {top['label']} - {top.get('description', '')}",
            raw_text=str(results)[:5000],
        )

    async def _describe_entity(self, name: str) -> ToolResult:
        entity_id = await self._find_entity_id(name)
        if not entity_id:
            return ToolResult(success=False, error=f"No Wikidata entity found for '{name}'")

        entity = await self._entity_data(entity_id)
        lines = []
        if entity:
            labels = entity.get("labels", {})
            en_label = labels.get("en", {})
            if en_label:
                lines.append(f"Label: {en_label.get('value', '')}")
            descs = entity.get("descriptions", {})
            en_desc = descs.get("en", {})
            if en_desc:
                lines.append(f"Description: {en_desc.get('value', '')}")

        query = f"""
        SELECT ?property ?propertyLabel ?value ?valueLabel WHERE {{
            wd:{entity_id} ?p ?statement .
            ?property wikibase:directClaim ?p .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT 50
        """
        bindings = await self._sparql_query(query)
        for b in bindings:
            prop = b.get("propertyLabel", {}).get("value", "")
            val = b.get("valueLabel", {}).get("value", b.get("value", {}).get("value", ""))
            lines.append(f"{prop}: {val}")

        snippet = "\n".join(lines[:25])
        return ToolResult(
            success=True,
            data=bindings,
            source_type="wikidata_sparql",
            source_url=f"https://www.wikidata.org/wiki/{entity_id}",
            title=f"Wikidata: {name}",
            snippet=snippet,
            raw_text=str(bindings)[:10000],
        )

    async def _corporate_query(self, company_name: str) -> ToolResult:
        entity_id = await self._find_entity_id(company_name)
        if not entity_id:
            return ToolResult(success=False, error=f"No Wikidata entity found for '{company_name}'")

        query = f"""
        SELECT ?item ?itemLabel ?relationship ?relatedEntity ?relatedEntityLabel WHERE {{
            wd:{entity_id} ?prop ?relatedEntity .
            ?item wdt:P31 wd:Q783794 .
            ?item ?propVal wd:{entity_id} .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT 30
        """
        bindings = await self._sparql_query(query)
        lines = []
        for b in bindings[:20]:
            rel = b.get("relatedEntityLabel", {}).get("value", "")
            item = b.get("itemLabel", {}).get("value", "")
            lines.append(f"{item} -> {rel}")
        snippet = "\n".join(lines)
        return ToolResult(
            success=True,
            data=bindings,
            source_type="wikidata_sparql",
            source_url=f"https://www.wikidata.org/wiki/{entity_id}",
            title=f"Wikidata corporate: {company_name}",
            snippet=snippet,
            raw_text=str(bindings)[:10000],
        )
