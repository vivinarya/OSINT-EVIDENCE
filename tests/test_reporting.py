import pytest
from src.reporting import ReportGenerator, EvidenceExplainer
from src.evidence_ledger import EvidenceLedger, Source


@pytest.fixture
def ledger():
    return EvidenceLedger()


@pytest.fixture
def sample_source():
    return Source(
        source_type="web_search",
        source_url="https://example.com/article",
        title="Test",
        snippet="Company X received $40M funding",
        raw_text="Full text",
        retrieved_at="2026-07-17T10:00:00Z",
        retrieval_tool="web_search",
    )


class TestReportGenerator:
    def test_empty_ledger(self):
        gen = ReportGenerator()
        report = gen.generate(EvidenceLedger(), "Test query")
        assert "Test query" in report
        assert "No corroborated claims" in report

    def test_with_claims(self, ledger, sample_source):
        gen = ReportGenerator()
        ledger.add_claim("Company X raised $40M", sample_source, confidence=0.8)
        report = gen.generate(ledger, "Investigate Company X")
        assert "Investigate Company X" in report
        assert "Company X raised $40M" in report
        assert "c_000" in report

    def test_html_export(self, ledger, sample_source):
        gen = ReportGenerator()
        ledger.add_claim("Test claim", sample_source)
        html = gen.export_html(ledger, "Test query")
        assert "DOCTYPE html" in html
        assert "Test claim" in html


class TestEvidenceExplainer:
    def test_explain_nonexistent(self, ledger):
        explainer = EvidenceExplainer(ledger)
        result = explainer.explain_claim("c_999")
        assert "No claim found" in result

    def test_explain_existing(self, ledger, sample_source):
        claim = ledger.add_claim("Test claim", sample_source)
        explainer = EvidenceExplainer(ledger)
        result = explainer.explain_claim(claim.claim_id)
        assert "Test claim" in result
        assert "web_search" in result
        assert "Reasoning Chain" in result

    def test_summary_empty(self, ledger):
        explainer = EvidenceExplainer(ledger)
        assert "No evidence" in explainer.summary()

    def test_summary_with_claims(self, ledger, sample_source):
        ledger.add_claim("Claim 1", sample_source, confidence=0.9)
        ledger.add_claim("Claim 2", sample_source, confidence=0.5)
        explainer = EvidenceExplainer(ledger)
        summary = explainer.summary()
        assert "Total claims:" in summary
        assert "0.70" in summary
