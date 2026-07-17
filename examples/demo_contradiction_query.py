"""Demo: Verify a claim that likely has contradictory sources.

Run: python -m examples.demo_contradiction_query

This demonstrates:
- Contradiction surfacing (conflicting reports flagged, not silently averaged)
- Honest uncertainty reporting
- Corroboration/contradiction graph building
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.llm_client import LLMClient
from src.agent.react_loop import InvestigativeAgent
from src.reporting import ReportGenerator
from src.verification import ContradictionDetector


async def main():
    query = "Verify the claim that WorkingFromHome Inc was involved in sanctions violations"

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

    print("\n⚠️ CONTRADICTION ANALYSIS")
    print("=" * 60)
    detector = ContradictionDetector()
    contradictions = detector.find_contradictions(ledger)
    if contradictions:
        print(f"Found {len(contradictions)} contradiction(s):")
        for c in contradictions:
            print(f"\n  Severity: {c['severity'].upper()}")
            print(f"  Claim A: {c['claim_a']['text']}")
            print(f"    Source: {c['claim_a']['source']}")
            print(f"  Claim B: {c['claim_b']['text']}")
            print(f"    Source: {c['claim_b']['source']}")
    else:
        print("  ✅ No contradictions found — sources are consistent.")

    print(f"\n📊 Summary: {len(ledger.claims)} claims, {len(ledger.sources)} sources")


if __name__ == "__main__":
    asyncio.run(main())
