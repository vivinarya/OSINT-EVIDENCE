from __future__ import annotations
from src.evidence_ledger import EvidenceLedger


class ContradictionDetector:
    def find_contradictions(self, ledger: EvidenceLedger) -> list[dict]:
        contradictions = []
        for claim in ledger.get_all_claims():
            for cid in claim.contradicting_claim_ids:
                other = ledger.get_claim(cid)
                if other and claim.claim_id < other.claim_id:
                    contradictions.append({
                        "claim_a": {"id": claim.claim_id, "text": claim.text, "source": claim.source.source_url},
                        "claim_b": {"id": other.claim_id, "text": other.text, "source": other.source.source_url},
                        "confidence_a": claim.confidence,
                        "confidence_b": other.confidence,
                        "severity": self._calculate_severity(claim, other),
                    })
        return sorted(contradictions, key=lambda c: c["severity"], reverse=True)

    def _calculate_severity(self, ca, cb) -> str:
        avg_conf = (ca.confidence + cb.confidence) / 2
        if avg_conf >= 0.7:
            return "high"
        if avg_conf >= 0.4:
            return "medium"
        return "low"

    def contradiction_report(self, ledger: EvidenceLedger) -> str:
        contradictions = self.find_contradictions(ledger)
        if not contradictions:
            return "No contradictions detected."

        lines = ["## Contradictions & Discrepancies\n"]
        for i, c in enumerate(contradictions[:10], 1):
            lines.append(f"### Contradiction {i} (Severity: {c['severity'].upper()})")
            lines.append(f"- Claim A [{c['claim_a']['id']}]: {c['claim_a']['text']}")
            lines.append(f"  - Source: {c['claim_a']['source']}")
            lines.append(f"- Claim B [{c['claim_b']['id']}]: {c['claim_b']['text']}")
            lines.append(f"  - Source: {c['claim_b']['source']}")
            lines.append("")
        return "\n".join(lines)
