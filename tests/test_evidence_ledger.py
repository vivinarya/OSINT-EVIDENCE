import pytest
from src.evidence_ledger import EvidenceLedger, Source, Claim


@pytest.fixture
def ledger():
    return EvidenceLedger()


@pytest.fixture
def sample_source():
    return Source(
        source_type="web_search",
        source_url="https://example.com/article",
        title="Test Article",
        snippet="Company X received $40M in Series B funding",
        raw_text="Full article text here...",
        retrieved_at="2026-07-17T10:00:00Z",
        retrieval_tool="web_search",
    )


class TestEvidenceLedger:
    def test_add_claim(self, ledger, sample_source):
        claim = ledger.add_claim("Company X raised $40M", sample_source, confidence=0.8)
        assert claim.claim_id == "c_000"
        assert claim.text == "Company X raised $40M"
        assert claim.confidence == 0.8
        assert len(ledger.claims) == 1

    def test_add_multiple_claims(self, ledger, sample_source):
        c1 = ledger.add_claim("Claim 1", sample_source)
        c2 = ledger.add_claim("Claim 2", sample_source)
        assert c1.claim_id == "c_000"
        assert c2.claim_id == "c_001"
        assert len(ledger.claims) == 2

    def test_link_claims_corroborate(self, ledger, sample_source):
        c1 = ledger.add_claim("Claim A", sample_source)
        c2 = ledger.add_claim("Claim B", sample_source)
        ledger.link_claims(c1.claim_id, c2.claim_id, "corroborates")
        assert c2.claim_id in c1.corroborating_claim_ids
        assert c1.claim_id in c2.corroborating_claim_ids

    def test_link_claims_contradict(self, ledger, sample_source):
        c1 = ledger.add_claim("Claim A", sample_source)
        c2 = ledger.add_claim("Claim B", sample_source)
        ledger.link_claims(c1.claim_id, c2.claim_id, "contradicts")
        assert c2.claim_id in c1.contradicting_claim_ids
        assert c1.claim_id in c2.contradicting_claim_ids

    def test_get_claim_by_id(self, ledger, sample_source):
        claim = ledger.add_claim("Test", sample_source)
        assert ledger.get_claim("c_000") == claim
        assert ledger.get_claim("nonexistent") is None

    def test_get_claims_by_source(self, ledger, sample_source):
        ledger.add_claim("C1", sample_source)
        ledger.add_claim("C2", sample_source)
        other = Source(
            source_type="web_page",
            source_url="https://other.com",
            title="",
            snippet="",
            raw_text="",
            retrieved_at="",
            retrieval_tool="web_scraper",
        )
        ledger.add_claim("C3", other)
        results = ledger.get_claims_by_source("https://example.com/article")
        assert len(results) == 2

    def test_to_dict(self, ledger, sample_source):
        ledger.add_claim("Test claim", sample_source, confidence=0.9)
        d = ledger.to_dict()
        assert "claims" in d
        assert "c_000" in d["claims"]
        assert d["claims"]["c_000"]["text"] == "Test claim"
        assert d["claims"]["c_000"]["confidence"] == 0.9

    def test_empty_ledger(self, ledger):
        assert len(ledger.get_all_claims()) == 0
        d = ledger.to_dict()
        assert d == {"claims": {}}


class TestSource:
    def test_default_timestamp(self):
        s = Source(
            source_type="web",
            source_url="https://x.com",
            title="",
            snippet="",
            raw_text="",
            retrieved_at="",
            retrieval_tool="test",
        )
        assert s.retrieved_at != ""

    def test_reliability_tier_default(self, sample_source):
        assert sample_source.reliability_tier == "low"


class TestClaim:
    def test_default_timestamp(self, sample_source):
        c = Claim(claim_id="c_000", text="Test", source=sample_source)
        assert c.timestamp != ""
