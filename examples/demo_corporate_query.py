"""Demo: Investigate a corporate entity.

Run: python -m examples.demo_corporate_query
Requires API keys in .env (works without them using mock/fallback).

This demonstrates:
- Autonomous planning (planner breaks query into sub-questions)
- Multi-tool execution (web search + multiple datasets)
- Evidence Ledger population with claims
- Confidence scoring and cross-referencing
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.llm_client import LLMClient
from src.agent.react_loop import InvestigativeAgent
from src.reporting import ReportGenerator, EvidenceExplainer
from src.verification import ContradictionDetector
from src.evidence_ledger.store import LedgerStore


async def main():
    query = "Map the corporate network and controversies around OpenAI"

    print(f"🔍 Investigating: {query}\n")
    print("=" * 60)

    llm = LLMClient()
    agent = InvestigativeAgent(llm)

    result = await agent.investigate(query)
    ledger = result["ledger"]

    print("\n📋 REPORT")
    print("=" * 60)
    gen = ReportGenerator(llm)
    report = gen.generate(ledger, query)
    print(report)

    print("\n🔗 CONTRADICTIONS")
    print("=" * 60)
    detector = ContradictionDetector()
    contradictions = detector.find_contradictions(ledger)
    if contradictions:
        for c in contradictions[:3]:
            print(f"  ⚠️ {c['severity'].upper()}: {c['claim_a']['text'][:80]}... vs {c['claim_b']['text'][:80]}...")
    else:
        print("  No contradictions detected.")

    if ledger.claims:
        first_id = list(ledger.claims.keys())[0]
        print(f"\n❓ EXPLAIN CLAIM {first_id}")
        print("=" * 60)
        explainer = EvidenceExplainer(ledger)
        print(explainer.explain_claim(first_id))

    store = LedgerStore("investigation_output.json")
    store.save(ledger)
    print(f"\n💾 Saved to investigation_output.json")


if __name__ == "__main__":
    asyncio.run(main())
