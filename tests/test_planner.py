from src.agent.planner import _diversify_plan


def test_diversify_plan_adds_broad_coverage_for_ambiguous_topics():
    plan = [
        {
            "question": "Search Epstein files",
            "tool": "web_search",
            "params": {"query": "Epstein files"},
        }
    ]

    diversified = _diversify_plan("Epstein files", plan)

    assert len(diversified) >= 4
    queries = [step["params"]["query"].lower() for step in diversified if step["tool"] == "web_search"]
    assert any("overview" in query or "background" in query for query in queries)
    assert any("timeline" in query or "latest" in query for query in queries)
    assert any("court" in query or "justice.gov" in query or "uscourts.gov" in query for query in queries)
    assert any("people" in query or "organizations" in query or "involved" in query for query in queries)


def test_diversify_plan_preserves_diverse_plans():
    plan = [
        {"question": "Overview", "tool": "web_search", "params": {"query": "topic overview"}},
        {"question": "Timeline", "tool": "web_search", "params": {"query": "topic timeline"}},
        {"question": "Court", "tool": "web_search", "params": {"query": "topic court filings"}},
        {"question": "People", "tool": "web_search", "params": {"query": "topic people involved"}},
    ]

    diversified = _diversify_plan("topic files", plan)

    assert len(diversified) == 4
    assert [step["params"]["query"] for step in diversified] == [
        "topic overview",
        "topic timeline",
        "topic court filings",
        "topic people involved",
    ]
