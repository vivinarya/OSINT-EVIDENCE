import pytest
from src.verification import ConfidenceScorer, ContradictionDetector
from src.evidence_ledger import EvidenceLedger, Source, Claim
from datetime import datetime, timezone


@pytest.fixture
def ledger():
    return EvidenceLedger()


@pytest.fixture
def scorer():
    return ConfidenceScorer()


class TestConfidenceScorer:
    def test_high_reliability_source(self, scorer):
        claim = Claim(
            claim_id="c_000",
            text="SEC filing shows revenue",
            source=Source(
                source_type="web",
                source_url="https://sec.gov/filing/123",
                title="",
                snippet="",
                raw_text="",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                retrieval_tool="web_search",
            ),
            corroborating_claim_ids=["c_001", "c_002"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        ledger = EvidenceLedger()
        ledger.claims["c_000"] = claim
        ledger.claims["c_001"] = Claim(
            claim_id="c_001", text="Corroboration", confidence=0.8,
            source=Source("web", "https://other.com", "", "", "", "", "web_search"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        ledger.claims["c_002"] = Claim(
            claim_id="c_002", text="Corroboration 2", confidence=0.7,
            source=Source("web", "https://third.com", "", "", "", "", "web_search"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        score = scorer.score_claim(claim, ledger)
        assert score > 0.5

    def test_low_reliability_source(self, scorer):
        claim = Claim(
            claim_id="c_000",
            text="Blog post claim",
            source=Source(
                source_type="web",
                source_url="https://unknown-blog.example.com/post",
                title="",
                snippet="",
                raw_text="",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                retrieval_tool="web_search",
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        ledger = EvidenceLedger()
        ledger.claims["c_000"] = claim
        score = scorer.score_claim(claim, ledger)
        assert score < 0.6


class TestContradictionDetector:
    def test_no_contradictions(self, ledger):
        detector = ContradictionDetector()
        assert detector.find_contradictions(ledger) == []

    def test_detects_contradictions(self, ledger):
        source = Source("web", "https://example.com", "", "", "", "", "web_search")
        c1 = ledger.add_claim("Claim A", source)
        c2 = ledger.add_claim("Claim B", source)
        ledger.link_claims(c1.claim_id, c2.claim_id, "contradicts")
        detector = ContradictionDetector()
        contradictions = detector.find_contradictions(ledger)
        assert len(contradictions) == 1
        assert contradictions[0]["claim_a"]["id"] == "c_000"
        assert contradictions[0]["claim_b"]["id"] == "c_001"
