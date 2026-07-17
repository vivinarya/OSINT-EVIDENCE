from __future__ import annotations
from src.config import STEP_CAP
from src.llm_client import LLMClient
from src.evidence_ledger import EvidenceLedger
from src.agent.planner import Planner
from src.agent.executor import Executor, _forward_message

REFLECT_PROMPT = """You are an investigative agent. Here is your investigation question:
{query}

Here is what you have learned so far:
{evidence_summary}

Do you have sufficient evidence to produce a complete report? 
- If YES, respond with: {{"decision": "report", "reasoning": "..."}}
- If NO, respond with: {{"decision": "continue", "reasoning": "...", "follow_up": "specific follow-up question"}}"""

REPORT_PROMPT = """You are an investigative analyst. Based on the evidence ledger below, produce a structured investigative report.

Every factual claim must include an inline citation marker like [c_001] referencing the claim_id from the evidence.

Evidence:
{evidence_json}

Write a report with sections:
1. Executive Summary
2. Key Findings (with inline citations)
3. Confirmed Claims (corroborated by 2+ sources)
4. Single-Source Claims
5. Contradictions & Discrepancies
6. Sources & Methodology

Return JSON with key "report" containing the report text."""


class InvestigativeAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.ledger = EvidenceLedger()
        self.planner = Planner(llm)
        self.executor = Executor(llm, self.ledger)

    async def investigate(self, query: str) -> dict:
        plan = await self.planner.plan(query)
        all_results = []
        step_count = 0

        if plan:
            batch = plan[:STEP_CAP]
            results = await self.executor.execute_plan(batch, parallel=True)
            all_results.extend(results)
            step_count += len(batch)

        evidence_summary = self._summarize_evidence()
        reflect = await self.llm.generate_json(
            REFLECT_PROMPT.format(query=query, evidence_summary=evidence_summary)
        )
        decision = reflect.get("decision", "continue") if isinstance(reflect, dict) else "continue"

        if decision != "report":
            follow_up = reflect.get("follow_up", "") if isinstance(reflect, dict) else ""
            if follow_up and step_count < STEP_CAP:
                adaptive_results = await self.executor.adaptive_search(follow_up, evidence_summary)
                all_results.extend(adaptive_results)

        if self.ledger.claims:
            evidence = _forward_message(list(self.ledger.claims.keys()), self.ledger)

        return await self._generate_report(query)

    async def _generate_report(self, query: str) -> dict:
        evidence_json = self.ledger.to_dict()
        prompt = REPORT_PROMPT.format(query=query, evidence_json=str(evidence_json)[:12000])
        response = await self.llm.generate_json(prompt)
        report_text = response.get("report", "") if isinstance(response, dict) else str(response)

        return {
            "query": query,
            "report": report_text,
            "ledger": self.ledger,
            "claim_count": len(self.ledger.claims),
            "source_count": len(self.ledger.sources),
            "evidence_json": evidence_json,
        }

    async def explain_claim(self, claim_id: str) -> dict | None:
        claim = self.ledger.get_claim(claim_id)
        if not claim:
            return None

        corroborating = [self.ledger.get_claim(cid) for cid in claim.corroborating_claim_ids]
        contradicting = [self.ledger.get_claim(cid) for cid in claim.contradicting_claim_ids]

        return {
            "claim": claim.text,
            "confidence": claim.confidence,
            "source_url": claim.source.source_url,
            "source_type": claim.source.source_type,
            "retrieval_tool": claim.source.retrieval_tool,
            "extraction_method": claim.extraction_method,
            "snippet": claim.source.snippet[:500] if claim.source.snippet else "",
            "corroborating_claims": [{"id": c.claim_id, "text": c.text, "source": c.source.source_url}
                                      for c in corroborating if c],
            "contradicting_claims": [{"id": c.claim_id, "text": c.text, "source": c.source.source_url}
                                      for c in contradicting if c],
            "reasoning_replay": self._build_reasoning_replay(claim),
        }

    def _build_reasoning_replay(self, claim) -> str:
        parts = [
            f"Step 1: The agent used the '{claim.source.retrieval_tool}' tool to retrieve information.",
            f"Step 2: Retrieved from: {claim.source.source_url}",
            f"Step 3: The '{claim.extraction_method}' method extracted this claim from the retrieved content.",
            f"Step 4: Confidence score of {claim.confidence:.2f} was assigned based on source reliability, corroboration, and recency.",
        ]
        if claim.corroborating_claim_ids:
            parts.append(f"Step 5: This claim is corroborated by {len(claim.corroborating_claim_ids)} other independent source(s).")
        if claim.contradicting_claim_ids:
            parts.append(f"Step 6: WARNING: This claim is contradicted by {len(claim.contradicting_claim_ids)} other source(s).")
        return "\n".join(parts)

    def _summarize_evidence(self) -> str:
        lines = []
        for cid, claim in self.ledger.claims.items():
            lines.append(f"[{cid}] {claim.text[:200]} (confidence: {claim.confidence:.2f}, source: {claim.source.source_url[:80]})")
        return "\n".join(lines) if lines else "No evidence gathered yet."

    def get_ledger(self) -> EvidenceLedger:
        return self.ledger
