from __future__ import annotations
import json
from pathlib import Path
from .schema import EvidenceLedger, Claim, Source


class LedgerStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else Path("evidence_ledger.json")

    def save(self, ledger: EvidenceLedger):
        data = ledger.to_dict()
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> EvidenceLedger:
        if not self.path.exists():
            return EvidenceLedger()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        ledger = EvidenceLedger()
        for cid, cdata in data.get("claims", {}).items():
            source = Source(
                source_type=cdata.get("source_type", "unknown"),
                source_url=cdata.get("source_url", ""),
                title="",
                snippet=cdata.get("retrieved_snippet", ""),
                raw_text="",
                retrieved_at=cdata.get("timestamp", ""),
                retrieval_tool=cdata.get("retrieval_tool", "unknown"),
            )
            claim = Claim(
                claim_id=cid,
                text=cdata["text"],
                source=source,
                confidence=cdata.get("confidence", 0.0),
                extraction_method=cdata.get("extraction_method", ""),
                timestamp=cdata.get("timestamp", ""),
            )
            claim.corroborating_claim_ids = cdata.get("corroborating_claim_ids", [])
            claim.contradicting_claim_ids = cdata.get("contradicting_claim_ids", [])
            ledger.claims[cid] = claim
        return ledger

    def export_report_json(self, ledger: EvidenceLedger) -> str:
        return json.dumps(ledger.to_dict(), indent=2)
