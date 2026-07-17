from __future__ import annotations
import asyncio
from src.evidence_ledger import EvidenceLedger, Claim
from src.llm_client import LLMClient

MATCH_PROMPT = """Given two claims, determine if they:
1. "corroborates" - the claims support each other / agree
2. "contradicts" - the claims conflict with each other
3. "unrelated" - the claims are about different things

Claim A: "{claim_a}"
Claim B: "{claim_b}"

Respond with exactly one word: corroborates, contradicts, or unrelated"""

DEBATE_PROMPT = """Two claims need adjudication. Analyze them carefully:

Claim A: "{claim_a}"
Claim B: "{claim_b}"

Round 1 — Identify what each claim asserts independently.
Round 2 — Check if they are compatible or mutually exclusive.
Round 3 — Adjudicate.

Return JSON: {{"relation": "corroborates|contradicts|unrelated", "reasoning": "..."}}"""


class CrossReferencer:
    def __init__(self, llm: LLMClient | None = None, use_debate: bool = True):
        self.llm = llm
        self.use_debate = use_debate

    def cross_reference(self, ledger: EvidenceLedger):
        claims = ledger.get_all_claims()
        for i, ca in enumerate(claims):
            for j, cb in enumerate(claims):
                if j <= i:
                    continue
                relation = self._compare_claims(ca, cb)
                if relation and relation != "unrelated":
                    ledger.link_claims(ca.claim_id, cb.claim_id, relation)

    def _compare_claims(self, ca: Claim, cb: Claim) -> str | None:
        text_a = ca.text.lower()
        text_b = cb.text.lower()
        common_words = set(text_a.split()) & set(text_b.split())
        if len(common_words) < 2:
            return "unrelated"

        if self.llm:
            result = self._llm_compare(ca.text, cb.text)
            if result:
                return result
        return self._heuristic_compare(text_a, text_b)

    def _heuristic_compare(self, text_a: str, text_b: str) -> str:
        overlap = len(set(text_a.split()) & set(text_b.split()))
        total = max(len(set(text_a.split())), 1)
        ratio = overlap / total
        if ratio > 0.6:
            return "corroborates"
        if ratio > 0.3:
            negations_a = any(w in text_a for w in ["not", "no", "never", "denies", "contradicts"])
            negations_b = any(w in text_b for w in ["not", "no", "never", "denies", "contradicts"])
            if negations_a != negations_b:
                return "contradicts"
            return "corroborates"
        return "unrelated"

    def _llm_compare(self, text_a: str, text_b: str) -> str | None:
        return None
