from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import urlparse
from src.evidence_ledger import EvidenceLedger, Claim
from src.config import SOURCE_RELIABILITY_TIERS


class ConfidenceScorer:
    def __init__(self):
        self.high_domains = set(SOURCE_RELIABILITY_TIERS["high"])
        self.medium_domains = set(SOURCE_RELIABILITY_TIERS["medium"])

    def score_claim(self, claim: Claim, ledger: EvidenceLedger) -> float:
        source_score = self._source_reliability(claim.source.source_url)
        corroboration_score = self._corroboration_score(claim, ledger)
        recency_score = self._recency_score(claim.timestamp)
        independence_score = self._independence_score(claim, ledger)

        weights = {"source": 0.30, "corroboration": 0.35, "recency": 0.15, "independence": 0.20}
        score = (
            source_score * weights["source"]
            + corroboration_score * weights["corroboration"]
            + recency_score * weights["recency"]
            + independence_score * weights["independence"]
        )
        return round(min(max(score, 0.0), 1.0), 3)

    def _source_reliability(self, url: str) -> float:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        if any(d in domain for d in self.high_domains):
            return 0.9
        if any(d in domain for d in self.medium_domains):
            return 0.6
        return 0.3

    def _corroboration_score(self, claim: Claim, ledger: EvidenceLedger) -> float:
        corroborators = len(claim.corroborating_claim_ids)
        if corroborators >= 3:
            return 1.0
        if corroborators == 2:
            return 0.85
        if corroborators == 1:
            return 0.65
        return 0.3

    def _recency_score(self, timestamp_str: str) -> float:
        try:
            claim_time = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)
            days_old = (now - claim_time).days
            if days_old <= 7:
                return 1.0
            if days_old <= 30:
                return 0.9
            if days_old <= 90:
                return 0.7
            if days_old <= 365:
                return 0.5
            return 0.3
        except (ValueError, TypeError):
            return 0.5

    def _independence_score(self, claim: Claim, ledger: EvidenceLedger) -> float:
        related_urls = set()
        related_urls.add(claim.source.source_url)
        for cid in claim.corroborating_claim_ids:
            c = ledger.get_claim(cid)
            if c:
                domain = urlparse(c.source.source_url).netloc
                related_urls.add(domain)
        independence = len(related_urls)
        if independence >= 3:
            return 1.0
        if independence == 2:
            return 0.7
        return 0.4

    def score_all(self, ledger: EvidenceLedger):
        for claim in ledger.get_all_claims():
            claim.confidence = self.score_claim(claim, ledger)
