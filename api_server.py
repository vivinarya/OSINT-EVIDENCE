from __future__ import annotations
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.llm_client import LLMClient
from src.agent.react_loop import InvestigativeAgent
from src.reporting import ReportGenerator, EvidenceExplainer
from src.verification import ContradictionDetector

app = FastAPI(title="OSINT Investigative Agent API")
_last_ledger = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/investigate")
async def investigate(req: QueryRequest):
    global _last_ledger
    llm = LLMClient()
    agent = InvestigativeAgent(llm)
    result = await agent.investigate(req.query)

    ledger = result["ledger"]
    all_claims = ledger.get_all_claims()
    contradictions = ContradictionDetector().find_contradictions(ledger)

    claims_out = []
    for c in sorted(all_claims, key=lambda x: x.confidence, reverse=True):
        claims_out.append({
            "id": c.claim_id,
            "text": c.text,
            "confidence": c.confidence,
            "source": {
                "source_type": c.source.source_type,
                "source_url": c.source.source_url,
                "retrieval_tool": c.source.retrieval_tool,
                "title": c.source.title,
            },
            "corroborating_claim_ids": c.corroborating_claim_ids,
            "contradicting_claim_ids": c.contradicting_claim_ids,
        })

    contradictions_out = []
    for cd in contradictions:
        contradictions_out.append({
            "id_a": cd["claim_a"]["id"],
            "id_b": cd["claim_b"]["id"],
            "severity": cd["severity"].upper(),
            "reason": "",
        })

    sources_out = []
    seen_sources = set()
    for c in all_claims:
        key = c.source.source_type
        if key not in seen_sources:
            seen_sources.add(key)
            sources_out.append({
                "source_type": c.source.source_type,
                "title": c.source.title or c.source.source_type,
            })

    _last_ledger = ledger

    return {
        "query": req.query,
        "claims": claims_out,
        "contradictions": contradictions_out,
        "sources": sources_out,
        "report": result.get("report", ""),
        "claim_count": len(claims_out),
        "source_count": len(sources_out),
    }


class ExplainRequest(BaseModel):
    claim_id: str


@app.post("/api/explain")
async def explain_claim(req: ExplainRequest):
    if not _last_ledger:
        return {"error": "No investigation data available. Run an investigation first."}
    explainer = EvidenceExplainer(_last_ledger)
    explanation = explainer.explain_claim(req.claim_id)
    return {"claim_id": req.claim_id, "explanation": explanation}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
