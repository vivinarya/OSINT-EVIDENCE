from __future__ import annotations
from src.evidence_ledger import EvidenceLedger


class EvidenceExplainer:
    def __init__(self, ledger: EvidenceLedger):
        self.ledger = ledger

    def explain_claim(self, claim_id: str) -> str:
        claim = self.ledger.get_claim(claim_id)
        if not claim:
            return f"No claim found with ID '{claim_id}'."

        lines = [f"Claim: {claim.text}", ""]
        lines.append(f"Claim ID: {claim.claim_id}")
        lines.append(f"Confidence: {claim.confidence:.2f}")
        lines.append(f"Source URL: {claim.source.source_url}")
        lines.append(f"Source Type: {claim.source.source_type}")
        lines.append(f"Retrieval Tool: {claim.source.retrieval_tool}")
        lines.append(f"Retrieved At: {claim.source.retrieved_at}")
        lines.append(f"Extraction Method: {claim.extraction_method}")
        lines.append("")

        lines.append("Retrieved Snippet:")
        lines.append(claim.source.snippet[:500] if claim.source.snippet else "")
        lines.append("")

        if claim.corroborating_claim_ids:
            lines.append(f"Corroborating Claims ({len(claim.corroborating_claim_ids)}):")
            for cid in claim.corroborating_claim_ids:
                other = self.ledger.get_claim(cid)
                if other:
                    lines.append(f"- {cid}: {other.text[:150]} (confidence {other.confidence:.2f})")
            lines.append("")

        if claim.contradicting_claim_ids:
            lines.append(f"Contradicting Claims ({len(claim.contradicting_claim_ids)}):")
            for cid in claim.contradicting_claim_ids:
                other = self.ledger.get_claim(cid)
                if other:
                    lines.append(f"- {cid}: {other.text[:150]} (confidence {other.confidence:.2f})")
            lines.append("")

        lines.append("Reasoning Chain:")
        lines.append(f"1. Tool call: {claim.source.retrieval_tool} was invoked")
        lines.append(f"2. Source: Retrieved from {claim.source.source_url}")
        lines.append(f"3. Extraction: {claim.extraction_method} extracted the claim from the source text")
        lines.append(f"4. Confidence: Scored at {claim.confidence:.2f} based on source reliability, corroboration, recency, and source independence")
        if claim.corroborating_claim_ids:
            lines.append(f"5. Corroboration: {len(claim.corroborating_claim_ids)} other independent claim(s) support this finding")
        if claim.contradicting_claim_ids:
            lines.append(f"6. Contradiction warning: {len(claim.contradicting_claim_ids)} other claim(s) conflict with this finding")

        return "\n".join(lines)

    def summary(self) -> str:
        claims = self.ledger.get_all_claims()
        if not claims:
            return "No evidence gathered yet."

        corroborated_count = sum(1 for c in claims if len(c.corroborating_claim_ids) >= 1)
        contradicted_count = sum(1 for c in claims if len(c.contradicting_claim_ids) >= 1)
        avg_conf = sum(c.confidence for c in claims) / len(claims) if claims else 0
        unique_sources = len(set(c.source.source_url for c in claims))

        return (
            f"Total claims: {len(claims)}\n"
            f"Unique sources: {unique_sources}\n"
            f"Corroborated claims: {corroborated_count}\n"
            f"Contradicted claims: {contradicted_count}\n"
            f"Average confidence: {avg_conf:.2f}\n"
        )
