"""
confidence_scorer.py — B.R.A.G Confidence Scoring Engine
==========================================================

Implements the B.R.A.G framework for RAG evidence quality assessment:

  B · Base Source Reliability  (30%)
  R · Retrieval Recency        (15%)
  A · Attestation/Corroboration(35%)   ← highest weight: multiple sources matter most
  G · Groundedness/Independence(20%)

Final score = (B×0.30) + (R×0.15) + (A×0.35) + (G×0.20)
Clamped to [0.0, 1.0], rounded to 3 decimal places.

Thresholds (used by EvidenceCard and ReportGenerator):
  ≥ 0.70  → HIGH    (green)
  0.40–0.69 → MEDIUM (amber)
  < 0.40  → LOW     (grey)
"""

from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import urlparse
from src.evidence_ledger import EvidenceLedger, Claim
from src.config import SOURCE_RELIABILITY_TIERS


class ConfidenceScorer:
    """
    Scores each Claim in an EvidenceLedger using the B.R.A.G composite formula.

    Call order:
      1. CrossReferencer.cross_reference(ledger)   ← must run FIRST to populate
                                                       corroborating_claim_ids
      2. ConfidenceScorer.score_all(ledger)         ← then scoring reads those links
    """

    def __init__(self):
        # Pre-load domain sets from config for O(1) lookup during scoring
        self.high_domains = set(SOURCE_RELIABILITY_TIERS["high"])
        self.medium_domains = set(SOURCE_RELIABILITY_TIERS["medium"])

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def score_claim(self, claim: Claim, ledger: EvidenceLedger) -> float:
        """
        Compute the B.R.A.G confidence score for a single claim.

        Parameters
        ----------
        claim  : The Claim to score. Its corroborating_claim_ids must already be
                 populated by CrossReferencer before calling this.
        ledger : Full EvidenceLedger — needed to look up corroborating claim sources
                 for the G (Groundedness/Independence) sub-score.

        Returns
        -------
        float in [0.0, 1.0] — the composite B.R.A.G confidence score.
        """
        # ── B: Base Source Reliability ──────────────────────────────────────
        # Checks the claim's source URL domain against tiered whitelist.
        source_score = self._source_reliability(claim.source.source_url)

        # ── A: Attestation / Corroboration ──────────────────────────────────
        # Counts how many other claims in the ledger support this one.
        # This is the highest-weighted component (0.35) because independent
        # agreement across sources is the strongest signal of truth.
        corroboration_score = self._corroboration_score(claim, ledger)

        # ── R: Retrieval Recency ─────────────────────────────────────────────
        # Uses the claim's own timestamp (time of retrieval) as a proxy for
        # freshness. Stale claims score lower — important for OSINT where
        # sanctions lists, corporate records, and news change frequently.
        recency_score = self._recency_score(claim.timestamp)

        # ── G: Groundedness / Source Independence ────────────────────────────
        # Checks whether corroborating claims come from *different* domains.
        # Three claims from the same website count less than three different sites.
        independence_score = self._independence_score(claim, ledger)

        # ── Weighted sum ─────────────────────────────────────────────────────
        weights = {
            "source": 0.30,          # B — domain trustworthiness
            "corroboration": 0.35,   # A — cross-source agreement (most important)
            "recency": 0.15,         # R — freshness of retrieval
            "independence": 0.20,    # G — domain diversity of corroborators
        }
        score = (
            source_score       * weights["source"]
            + corroboration_score * weights["corroboration"]
            + recency_score       * weights["recency"]
            + independence_score  * weights["independence"]
        )
        return round(min(max(score, 0.0), 1.0), 3)

    def score_all(self, ledger: EvidenceLedger):
        """
        Re-score every claim in the ledger in place.
        Called by ReportGenerator.generate() after cross-referencing is complete.
        Overwrites the seed confidence values set by ClaimExtractor.
        """
        for claim in ledger.get_all_claims():
            claim.confidence = self.score_claim(claim, ledger)

    # ─────────────────────────────────────────────────────────────────────────
    # B — Base Source Reliability
    # ─────────────────────────────────────────────────────────────────────────

    def _source_reliability(self, url: str) -> float:
        """
        B component (weight: 0.30).

        Parses the URL's netloc (e.g. "www.reuters.com" → "reuters.com") and
        checks membership in SOURCE_RELIABILITY_TIERS from src/config.py.

        Returns
        -------
        0.9  — "high" tier  (sec.gov, icij.org, reuters.com, bloomberg.com, …)
        0.6  — "medium" tier (nytimes.com, bbc.com, theguardian.com, …)
        0.3  — "low" / unknown (any domain not in the whitelist)

        Example contributions to final score (at weight 0.30):
          reuters.com  → 0.9 × 0.30 = 0.27
          nytimes.com  → 0.6 × 0.30 = 0.18
          unknown blog → 0.3 × 0.30 = 0.09
        """
        domain = urlparse(url).netloc.lower().replace("www.", "")
        if any(d in domain for d in self.high_domains):
            return 0.9  # verified high-tier journalism / government / OSINT DB
        if any(d in domain for d in self.medium_domains):
            return 0.6  # reputable but not primary source
        return 0.3      # unknown, blog, or scraped page

    # ─────────────────────────────────────────────────────────────────────────
    # A — Attestation / Corroboration
    # ─────────────────────────────────────────────────────────────────────────

    def _corroboration_score(self, claim: Claim, ledger: EvidenceLedger) -> float:
        """
        A component (weight: 0.35 — the most impactful factor).

        Counts how many other claims in the ledger corroborate this one.
        These links are set by CrossReferencer.cross_reference() using:
          · Word-overlap heuristic (Jaccard-like ratio)
          · Optional LLM adjudication via DEBATE_PROMPT

        Returns
        -------
        1.00 — 3 or more corroborators  (strong consensus)
        0.85 — 2 corroborators          (good agreement)
        0.65 — 1 corroborator           (weakly supported)
        0.30 — 0 corroborators          (sole source, treat with caution)

        Example contributions to final score (at weight 0.35):
          3+ corroborators → 1.00 × 0.35 = 0.350
          1  corroborator  → 0.65 × 0.35 = 0.228
          0  corroborators → 0.30 × 0.35 = 0.105
        """
        corroborators = len(claim.corroborating_claim_ids)
        if corroborators >= 3:
            return 1.0
        if corroborators == 2:
            return 0.85
        if corroborators == 1:
            return 0.65
        return 0.3  # isolated claim — most common for niche OSINT findings

    # ─────────────────────────────────────────────────────────────────────────
    # R — Retrieval Recency
    # ─────────────────────────────────────────────────────────────────────────

    def _recency_score(self, timestamp_str: str) -> float:
        """
        R component (weight: 0.15).

        Uses the Claim.timestamp (UTC ISO-8601) — the moment the data was
        retrieved — as a proxy for freshness. More recent = more reliable
        for OSINT investigations where records change frequently.

        Returns
        -------
        1.0  — ≤ 7 days old    (very fresh)
        0.9  — 8–30 days old   (current month)
        0.7  — 31–90 days old  (recent quarter)
        0.5  — 91–365 days old (within the year)
        0.3  — > 1 year old    (potentially stale)
        0.5  — on parse error  (neutral fallback)

        Note: Since the agent retrieves data live, most claims will score 1.0
        here. This component matters more for cached/historical data sources.
        """
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
            return 0.5  # neutral fallback for missing/malformed timestamps

    # ─────────────────────────────────────────────────────────────────────────
    # G — Groundedness / Source Independence
    # ─────────────────────────────────────────────────────────────────────────

    def _independence_score(self, claim: Claim, ledger: EvidenceLedger) -> float:
        """
        G component (weight: 0.20).

        Measures whether corroborating claims come from *different* domains.
        This guards against "echo chamber" corroboration — e.g., three Reuters
        articles all citing each other should not get the same boost as three
        completely independent sources (Reuters + SEC + ICIJ).

        Algorithm
        ---------
        1. Start a set with the current claim's source domain.
        2. For each corroborating claim ID, look up that claim in the ledger
           and add its domain to the set.
        3. The count of distinct domains is the "independence" value.

        Returns
        -------
        1.0  — 3+ distinct source domains
        0.7  — 2 distinct source domains
        0.4  — only 1 domain (all corroborators from same site)

        Example contributions to final score (at weight 0.20):
          3+ distinct domains → 1.0 × 0.20 = 0.200
          1 domain only       → 0.4 × 0.20 = 0.080
        """
        related_urls = set()
        # Always include the claim's own source domain
        related_urls.add(claim.source.source_url)
        # Collect distinct domains from all corroborating claims
        for cid in claim.corroborating_claim_ids:
            c = ledger.get_claim(cid)
            if c:
                # Use netloc (domain) not full URL — same site, different pages = 1 domain
                domain = urlparse(c.source.source_url).netloc
                related_urls.add(domain)
        independence = len(related_urls)
        if independence >= 3:
            return 1.0
        if independence == 2:
            return 0.7
        return 0.4
