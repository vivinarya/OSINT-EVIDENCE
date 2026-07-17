from __future__ import annotations
from src.llm_client import LLMClient

PLANNER_PROMPT = """You are an investigative research planner. Given an open-ended investigative question, break it down into sub-questions that can be researched independently (parallel-safe).

Your plan must maximize source diversity and angle coverage. For ambiguous topics, scandals, legal matters, leaked files, investigations, conflicts, or major public controversies, do not produce a single generic web search. Produce multiple searches that cover different angles such as:
- overview / background
- latest reporting or timeline
- court filings / official documents / government sources where applicable
- named people, organizations, or entities involved
- critiques, contradictions, or disputed interpretations

For each sub-question, specify:
1. The question text
2. Which tool to use (choose from the list below)
3. What parameters to pass to the tool

Available tools:
- wikidata: Query Wikidata for entity data (params: entity, query_type: describe|corporate|search) - NO API KEY NEEDED
- icij_data: Query local ICIJ Offshore Leaks data (params: entity, query_type: search_entity|search_officer|search_intermediary|get_entity_relationships) - NO API KEY NEEDED
- ofac_sdn: Query the OFAC sanctions list for blocked entities (params: query, country, program) - NO API KEY NEEDED
- gdelt: Query GDELT conflict/event data for recent events globally (params: country, event_type, actor, quad_class, limit, days_back) - NO API KEY NEEDED
- opensanctions: Sanctions/watchlist search (params: entity) - NO API KEY NEEDED
- wayback: Check archived version of a URL (params: url) - NO API KEY NEEDED
- web_search: General web search (params: query, max_results) - works with any API key or free DuckDuckGo fallback
- firecrawl_scraper: Scrape a specific URL for clean content (params: url)
- firecrawl_extract: Extract structured JSON data from a URL via LLM (params: url, prompt)

NOTE: opencorporates is a paid service and unavailable. Always use web_search for general web lookups.
WEB_SEARCH IS FREE AND WORKS FOR ANY QUERY - use it for every investigation.

IMPORTANT:
- Prefer 4 to 6 steps for broad or ambiguous topics.
- Avoid repeating the exact same query wording across steps.
- Use different query formulations that are likely to surface different publishers and different evidence types.
- If the topic mentions files, leaks, records, investigation, indictment, lawsuit, court, or testimony, at least one step must target official or legal-document coverage.
- You must respond with ONLY valid JSON. No explanations, no markdown, no code fences.

Return a JSON array of objects with keys: "question", "tool", "params".
params is an object with tool-specific parameters.
Do NOT include any text before or after the JSON.

Example:
[{{"question": "Find profile of entity", "tool": "wikidata", "params": {{"entity": "Mossack Fonseca", "query_type": "describe"}}}}]

Investigation question: {query}

Plan (up to 6 parallel-safe sub-questions):"""

AMBIGUOUS_MARKERS = (
    "files", "leaks", "records", "investigation", "probe", "case", "scandal",
    "lawsuit", "indictment", "court", "testimony", "hearing", "report",
)


def _is_ambiguous_topic(query: str) -> bool:
    lower = query.lower()
    return any(marker in lower for marker in AMBIGUOUS_MARKERS) or len(lower.split()) <= 4


def _default_diverse_plan(query: str) -> list[dict]:
    return [
        {
            "question": f"Get a broad overview of {query}",
            "tool": "web_search",
            "params": {"query": f"{query} overview background", "max_results": 6},
        },
        {
            "question": f"Find recent reporting and timeline coverage for {query}",
            "tool": "web_search",
            "params": {"query": f"{query} latest timeline reporting", "max_results": 6},
        },
        {
            "question": f"Find official or legal-document coverage for {query}",
            "tool": "web_search",
            "params": {"query": f"{query} court filing documents testimony site:gov OR site:uscourts.gov OR site:justice.gov", "max_results": 6},
        },
        {
            "question": f"Identify major people and organizations connected to {query}",
            "tool": "web_search",
            "params": {"query": f"{query} key people organizations involved", "max_results": 6},
        },
        {
            "question": f"Find disputed interpretations, rebuttals, or contradictions around {query}",
            "tool": "web_search",
            "params": {"query": f"{query} criticism disputed claims contradictions", "max_results": 6},
        },
    ]


def _normalize_step(step: dict, fallback_query: str) -> dict:
    if not isinstance(step, dict):
        return {
            "question": fallback_query,
            "tool": "web_search",
            "params": {"query": fallback_query, "max_results": 6},
        }

    tool = step.get("tool") or "web_search"
    question = step.get("question") or fallback_query
    params = step.get("params") if isinstance(step.get("params"), dict) else {}
    if tool == "web_search":
        params.setdefault("query", question)
        params.setdefault("max_results", 6)
    return {"question": question, "tool": tool, "params": params}


def _dedupe_plan(plan: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for step in plan:
        query = (step.get("params", {}).get("query") or step.get("question") or "").strip().lower()
        key = (step.get("tool"), query)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(step)
    return deduped


def _diversify_plan(query: str, plan: list[dict]) -> list[dict]:
    normalized = [_normalize_step(step, query) for step in plan]
    if not _is_ambiguous_topic(query):
        return _dedupe_plan(normalized)[:6]

    search_queries = [
        (step.get("params", {}) or {}).get("query", "").strip().lower()
        for step in normalized
        if step.get("tool") == "web_search"
    ]
    unique_searches = {q for q in search_queries if q}

    if len(unique_searches) >= 4:
        return _dedupe_plan(normalized)[:6]

    merged = normalized + _default_diverse_plan(query)
    return _dedupe_plan(merged)[:6]


class Planner:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def plan(self, query: str) -> list[dict]:
        prompt = PLANNER_PROMPT.format(query=query)
        response = await self.llm.generate_json(prompt)
        plan = response if isinstance(response, list) else response.get("plan", [response])
        return _diversify_plan(query, plan)
