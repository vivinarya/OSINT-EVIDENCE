from __future__ import annotations
from src.llm_client import LLMClient

PLANNER_PROMPT = """You are an investigative research planner. Given an open-ended investigative question, break it down into sub-questions that can be researched independently (parallel-safe).

For each sub-question, specify:
1. The question text
2. Which tool to use (choose from the list below)
3. What parameters to pass to the tool

Available tools:
- wikidata: Query Wikidata for entity data (params: entity, query_type: describe|corporate|search) — NO API KEY NEEDED
- icij_data: Query local ICIJ Offshore Leaks data (params: entity, query_type: search_entity|search_officer|search_intermediary|get_entity_relationships) — NO API KEY NEEDED
- ofac_sdn: Query the OFAC sanctions list for blocked entities (params: query, country, program) — NO API KEY NEEDED
- gdelt: Query GDELT conflict/event data for recent events globally (params: country, event_type, actor, quad_class, limit, days_back) — NO API KEY NEEDED
- opensanctions: Sanctions/watchlist search (params: entity) — NO API KEY NEEDED
- wayback: Check archived version of a URL (params: url) — NO API KEY NEEDED
- web_search: General web search (params: query) — works with any API key or free DuckDuckGo fallback
- firecrawl_scraper: Scrape a specific URL for clean content (params: url)
- firecrawl_extract: Extract structured JSON data from a URL via LLM (params: url, prompt)

NOTE: opencorporates is a paid service and unavailable. Always use web_search for general web lookups.
WEB_SEARCH IS FREE AND WORKS FOR ANY QUERY — use it for every investigation.

IMPORTANT: You must respond with ONLY valid JSON. No explanations, no markdown, no code fences.

Return a JSON array of objects with keys: "question", "tool", "params".
params is an object with tool-specific parameters.
Do NOT include any text before or after the JSON.

Example:
[{{"question": "Find profile of entity", "tool": "wikidata", "params": {{"entity": "Mossack Fonseca", "query_type": "describe"}}}}]

Investigation question: {query}

Plan (up to 6 parallel-safe sub-questions):"""


class Planner:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def plan(self, query: str) -> list[dict]:
        prompt = PLANNER_PROMPT.format(query=query)
        response = await self.llm.generate_json(prompt)
        plan = response if isinstance(response, list) else response.get("plan", [response])
        for item in plan:
            item.setdefault("params", {})
        return plan[:6]
