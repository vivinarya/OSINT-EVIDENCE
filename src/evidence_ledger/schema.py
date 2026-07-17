"""
schema.py — Evidence Ledger Data Models
========================================

B.R.A.G RAG Confidence Framework
----------------------------------
Every Claim in the ledger carries a `confidence` score (0.0–1.0) computed
by the ConfidenceScorer in src/verification/confidence_scorer.py.

The score is a weighted sum of four components, following the B.R.A.G model:

  B — Base Source Reliability    (weight: 0.30)
      How trustworthy is the origin domain?
      · High tier  (sec.gov, icij.org, reuters.com …) → 0.9
      · Medium tier (nytimes.com, bbc.com …)           → 0.6
      · Low / unknown domains                          → 0.3
      Configured in src/config.py → SOURCE_RELIABILITY_TIERS

  R — Retrieval Recency           (weight: 0.15)
      When was the source retrieved/published?
      · ≤ 7 days  → 1.0
      · ≤ 30 days → 0.9
      · ≤ 90 days → 0.7
      · ≤ 365 days → 0.5
      · Older      → 0.3

  A — Attestation (Corroboration)  (weight: 0.35)
      How many *other* independent claims corroborate this one?
      · 3+ corroborators → 1.0
      · 2  corroborators → 0.85
      · 1  corroborator  → 0.65
      · 0  (sole claim)  → 0.3
      Corroboration links are established by CrossReferencer (NLP overlap + LLM adjudication)

  G — Groundedness / Independence  (weight: 0.20)
      Are corroborating claims from *different* domains (source independence)?
      · 3+ distinct domains → 1.0
      · 2 distinct domains  → 0.7
      · 1 domain only       → 0.4

Final formula:
  confidence = (B × 0.30) + (R × 0.15) + (A × 0.35) + (G × 0.20)
  clamped to [0.0, 1.0], rounded to 3 decimal places.

Initial confidence seeding (before B.R.A.G scoring):
  ClaimExtractor pre-assigns a seed value:
    · 0.65  — sentence matched a VALUABLE_PATTERN (e.g. contains "$", "charged", "founded in")
    · 0.50  — sentence is long enough and starts with a capital letter
  This seed is overwritten by score_all() during ReportGenerator.generate().
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Source:
    """
    Represents a single evidence source retrieved during investigation.

    Fields
    ------
    source_type     : Retrieval tool category (e.g. "web_search", "firecrawl_search",
                      "wikidata_sparql", "icij_offshore_leaks", "ofac_sdn")
    source_url      : The canonical URL of the document/page the data came from.
                      Used by ConfidenceScorer._source_reliability() to look up
                      the domain against SOURCE_RELIABILITY_TIERS.
    title           : Page/document title from the retrieval tool.
    snippet         : Short text excerpt from the source (first ~200 chars).
    raw_text        : Full raw text of the retrieved document.
    retrieved_at    : ISO-8601 UTC timestamp of when retrieval happened.
                      Used by ConfidenceScorer._recency_score() (R in B.R.A.G).
    retrieval_tool  : Name of the tool that fetched this source (e.g. "web_search").
    reliability_tier: "high" | "medium" | "low" — pre-classified tier used as
                      a shortcut. The scorer re-derives this from the URL domain.
    """
    source_type: str
    source_url: str
    title: str
    snippet: str
    raw_text: str
    retrieved_at: str
    retrieval_tool: str
    reliability_tier: str = "low"

    def __post_init__(self):
        if not self.retrieved_at:
            self.retrieved_at = datetime.now(timezone.utc).isoformat()


@dataclass
class Claim:
    """
    Represents a single factual assertion extracted from a Source.

    The `confidence` field is the new geometric CS score normalised to 0.0–1.0.
    (CS/100, where CS = (SA×TF)×(CC×NI)×100)

    Logic States (confidence_state):
      VERIFIED_FACT  — CS ≥ 65, no contradictions, multi-source agreement
      BREAKING_CLAIM — CS < 50, no contradictions, sole/fresh source
      ACTIVE_DISPUTE — Contradiction detected, not definitively debunked
      DEBUNKED       — High-authority counter-claim with strong debunk signal
      UNSCORED       — Orchestrator has not yet run on this claim
    """
    claim_id: str
    text: str
    source: Source
    confidence: float = 0.0            # 0.0–1.0 (CS/100) — backwards compatible
    corroborating_claim_ids: list[str] = field(default_factory=list)
    contradicting_claim_ids: list[str] = field(default_factory=list)
    extraction_method: str = ""
    timestamp: str = ""

    # ── Multi-agent scoring fields (set by ScoringOrchestrator) ─────────────
    confidence_raw: float = 0.0        # CS on 0–100 scale
    confidence_state: str = "UNSCORED" # logic state
    source_authority: float = 0.0      # SA component (Source Tagger Agent)
    temporal_factor: float = 1.0       # TF component (Temporal Agent)
    corroboration_score: float = 0.0   # CC component (Network Graph Agent)
    network_independence: float = 0.0  # NI component (Network Graph Agent)
    claim_type: str = ""               # "static"|"dynamic_high"|"dynamic_medium"|"dynamic_low"
    echo_chamber: bool = False         # True if corroborators share same domain family
    decay_lambda: float = 0.0          # λ used in TF = e^(-λ·t)
    scoring_notes: list[str] = field(default_factory=list)  # per-agent reasoning

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class EvidenceLedger:
    """
    In-memory store for all Claims and Sources gathered during an investigation.

    Lifecycle
    ---------
    1. InvestigativeAgent populates the ledger via tools (web search, OSINT DBs, etc.)
    2. CrossReferencer.cross_reference(ledger) → links corroborating/contradicting claims
    3. ConfidenceScorer.score_all(ledger)      → computes B.R.A.G scores
    4. ContradictionDetector.find_contradictions(ledger) → surfaces conflicts
    5. ReportGenerator.generate(ledger, query) → produces the final report text
    6. api_server.py serialises ledger → JSON → frontend
    """

    def __init__(self):
        self.claims: dict[str, Claim] = {}
        self.sources: dict[str, Source] = {}
        self._next_id: int = 0

    def _next_claim_id(self) -> str:
        cid = f"c_{self._next_id:03d}"
        self._next_id += 1
        return cid

    def add_claim(self, text: str, source: Source, confidence: float = 0.0,
                  extraction_method: str = "") -> Claim:
        claim = Claim(
            claim_id=self._next_claim_id(),
            text=text,
            source=source,
            confidence=confidence,
            extraction_method=extraction_method,
        )
        self.claims[claim.claim_id] = claim
        return claim

    def add_source(self, source: Source) -> str:
        key = f"{source.source_type}::{source.source_url}"
        self.sources[key] = source
        return key

    def link_claims(self, claim_a: str, claim_b: str, relation: str):
        """
        Bidirectionally link two claims.
        - "corroborates" → boosts Attestation (A) score for both claims.
        - "contradicts"  → adds to contradicting_claim_ids for both (surfaced as conflicts).
        """
        if relation == "corroborates":
            if claim_b not in self.claims[claim_a].corroborating_claim_ids:
                self.claims[claim_a].corroborating_claim_ids.append(claim_b)
            if claim_a not in self.claims[claim_b].corroborating_claim_ids:
                self.claims[claim_b].corroborating_claim_ids.append(claim_a)
        elif relation == "contradicts":
            if claim_b not in self.claims[claim_a].contradicting_claim_ids:
                self.claims[claim_a].contradicting_claim_ids.append(claim_b)
            if claim_a not in self.claims[claim_b].contradicting_claim_ids:
                self.claims[claim_b].contradicting_claim_ids.append(claim_a)

    def get_claim(self, claim_id: str) -> Claim | None:
        return self.claims.get(claim_id)

    def get_all_claims(self) -> list[Claim]:
        return list(self.claims.values())

    def get_claims_by_source(self, source_url: str) -> list[Claim]:
        return [c for c in self.claims.values() if c.source.source_url == source_url]

    def to_dict(self) -> dict:
        return {
            "claims": {
                cid: {
                    "claim_id": c.claim_id,
                    "text": c.text,
                    "source_url": c.source.source_url,
                    "source_type": c.source.source_type,
                    "retrieved_snippet": c.source.snippet[:200] if c.source.snippet else "",
                    "retrieval_tool": c.source.retrieval_tool,
                    "extraction_method": c.extraction_method,
                    "confidence": c.confidence,
                    "corroborating_claim_ids": c.corroborating_claim_ids,
                    "contradicting_claim_ids": c.contradicting_claim_ids,
                    "timestamp": c.timestamp,
                }
                for cid, c in self.claims.items()
            }
        }
