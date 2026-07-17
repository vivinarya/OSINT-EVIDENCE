from __future__ import annotations
from src.evidence_ledger import EvidenceLedger, Claim
from src.verification import ConfidenceScorer, CrossReferencer, ContradictionDetector
from src.llm_client import LLMClient


class ReportGenerator:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm
        self.scorer = ConfidenceScorer()
        self.cross_referencer = CrossReferencer(llm)
        self.contradiction_detector = ContradictionDetector()

    def generate(self, ledger: EvidenceLedger, query: str) -> str:
        self.scorer.score_all(ledger)
        self.cross_referencer.cross_reference(ledger)

        claims = ledger.get_all_claims()
        corroborated = [c for c in claims if len(c.corroborating_claim_ids) >= 1]
        single_source = [c for c in claims if len(c.corroborating_claim_ids) == 0]
        high_conf = [c for c in claims if c.confidence >= 0.7]
        medium_conf = [c for c in claims if 0.4 <= c.confidence < 0.7]
        low_conf = [c for c in claims if c.confidence < 0.4]

        contradictions = self.contradiction_detector.find_contradictions(ledger)

        sections = []
        sections.append(f"# Investigative Report: {query}\n")
        sections.append(f"**Claims found:** {len(claims)} | **Sources:** {len(ledger.sources)}\n")

        sections.append("## Executive Summary\n")
        if high_conf:
            sections.append(f"- **{len(high_conf)} high-confidence claims** established\n")
        if contradictions:
            sections.append(f"- **{len(contradictions)} contradictions detected** — see discrepancies section\n")
        if corroborated:
            sections.append(f"- **{len(corroborated)} claims corroborated** by multiple independent sources\n")
        sections.append("")

        sections.append("## Key Findings\n")
        for c in sorted(claims, key=lambda x: x.confidence, reverse=True)[:15]:
            marker = "✅" if len(c.corroborating_claim_ids) >= 1 else "📄"
            sections.append(f"- {marker} {c.text} [{c.claim_id}] (confidence: {c.confidence:.2f})")
        sections.append("")

        sections.append("## Corroborated Claims (2+ sources)\n")
        corr_found = False
        for c in sorted(corroborated, key=lambda x: len(x.corroborating_claim_ids), reverse=True):
            if len(c.corroborating_claim_ids) >= 1:
                corr_found = True
                sources = [c.source.source_url]
                for cid in c.corroborating_claim_ids[:3]:
                    other = ledger.get_claim(cid)
                    if other:
                        sources.append(other.source.source_url)
                sections.append(f"- ✅ {c.text} [{c.claim_id}]\n  - Sources: {', '.join(set(sources))}")
        if not corr_found:
            sections.append("- No corroborated claims found.\n")
        sections.append("")

        sections.append("## Single-Source Claims\n")
        for c in single_source:
            sections.append(f"- 📄 {c.text} [{c.claim_id}] (confidence: {c.confidence:.2f})")
            sections.append(f"  - Source: {c.source.source_url}")
        sections.append("")

        if contradictions:
            sections.append("## Contradictions & Discrepancies\n")
            for i, cd in enumerate(contradictions[:10], 1):
                severity = cd["severity"].upper()
                sections.append(f"### Contradiction {i} (Severity: {severity})")
                sections.append(f"- Claim A [{cd['claim_a']['id']}]: {cd['claim_a']['text']}")
                sections.append(f"  - Source: {cd['claim_a']['source']} (confidence: {cd['confidence_a']:.2f})")
                sections.append(f"- Claim B [{cd['claim_b']['id']}]: {cd['claim_b']['text']}")
                sections.append(f"  - Source: {cd['claim_b']['source']} (confidence: {cd['confidence_b']:.2f})")
                sections.append("")

        sections.append("## Sources & Methodology\n")
        seen_urls = set()
        for c in claims:
            if c.source.source_url not in seen_urls:
                seen_urls.add(c.source.source_url)
                sections.append(f"- [{c.source.source_type}] {c.source.source_url}")
                sections.append(f"  - Retrieved via: {c.source.retrieval_tool} at {c.source.retrieved_at}")

        return "\n".join(sections)

    def export_html(self, ledger: EvidenceLedger, query: str) -> str:
        report_text = self.generate(ledger, query)
        claims = ledger.get_all_claims()
        contradictions = self.contradiction_detector.find_contradictions(ledger)

        claim_rows = ""
        for c in claims:
            corr_badge = f'<span class="badge corroborated">Corroborated ({len(c.corroborating_claim_ids)})</span>' if c.corroborating_claim_ids else ""
            contra_badge = f'<span class="badge contradicted">Contradicted ({len(c.contradicting_claim_ids)})</span>' if c.contradicting_claim_ids else ""
            claim_rows += f"""
            <tr>
                <td><a href="#claim-{c.claim_id}" class="claim-link">{c.claim_id}</a></td>
                <td>{c.text[:150]}</td>
                <td>{c.confidence:.2f}</td>
                <td>{corr_badge} {contra_badge}</td>
                <td><a href="{c.source.source_url}" target="_blank">source</a></td>
            </tr>"""

        contra_section = ""
        if contradictions:
            contra_items = "".join(
                f'<li><strong>High:</strong> "{c["claim_a"]["text"][:100]}..." vs "{c["claim_b"]["text"][:100]}..."</li>'
                for c in contradictions if c["severity"] == "high"
            )
            if contra_items:
                contra_section = f"<h2>⚠️ Contradictions</h2><ul>{contra_items}</ul>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>OSINT Report: {query[:60]}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 960px; margin: 0 auto; padding: 2rem; background: #0f1117; color: #e1e4e8; }}
  h1, h2 {{ color: #f0f6fc; border-bottom: 1px solid #30363d; padding-bottom: 0.3rem; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ padding: 0.5rem; text-align: left; border-bottom: 1px solid #21262d; }}
  th {{ background: #161b22; color: #8b949e; text-transform: uppercase; font-size: 0.8rem; }}
  tr:hover {{ background: #161b22; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.75rem; }}
  .corroborated {{ background: #1b4026; color: #7ee787; }}
  .contradicted {{ background: #4a1c1c; color: #ff7b72; }}
  .claim-link {{ color: #58a6ff; text-decoration: none; }}
  .claim-link:hover {{ text-decoration: underline; }}
  a {{ color: #58a6ff; }}
  .confidence-bar {{ height: 4px; background: #30363d; border-radius: 2px; margin-top: 2px; }}
  .confidence-fill {{ height: 100%; border-radius: 2px; background: linear-gradient(90deg, #f85149, #d2a8ff, #3fb950); }}
</style>
</head>
<body>
  <h1>Investigative Report: {query}</h1>
  <p><strong>{len(claims)} claims</strong> from <strong>{len(set(c.source.source_url for c in claims))} sources</strong></p>
  {contra_section}
  <h2>Evidence Ledger</h2>
  <table>
    <tr><th>ID</th><th>Claim</th><th>Confidence</th><th>Flags</th><th>Source</th></tr>
    {claim_rows}
  </table>
  <pre style="background:#161b22;padding:1rem;border-radius:6px;overflow-x:auto;white-space:pre-wrap;font-size:0.85rem;">{report_text[:3000]}</pre>
</body>
</html>"""
