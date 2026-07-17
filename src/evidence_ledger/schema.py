from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Source:
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
    claim_id: str
    text: str
    source: Source
    confidence: float = 0.0
    corroborating_claim_ids: list[str] = field(default_factory=list)
    contradicting_claim_ids: list[str] = field(default_factory=list)
    extraction_method: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class EvidenceLedger:
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
