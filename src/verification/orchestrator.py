"""
orchestrator.py — Central Scoring Orchestrator
===============================================
Coordinates all 4 specialist agents and computes the final Confidence Score.

Formula:
  CS = (SA × TF) × (CC × NI) × 100

Agents run in two phases:
  Phase 1 (parallel): SourceTaggerAgent + TemporalAgent + NetworkGraphAgent
  Phase 2 (serial):   AdversarialAgent (needs corroboration graph from Phase 1)

Logic States (per-claim):
  VERIFIED_FACT  — CS ≥ 65 and no active contradiction
  BREAKING_CLAIM — CS < 50 and no contradiction (sole/fresh source)
  ACTIVE_DISPUTE — Contradiction found but not definitively debunked
  DEBUNKED       — High-authority counter-claim, debunk_score ≥ 0.60

Output on Claim object:
  .confidence       — normalised 0.0–1.0 (CS/100) for backwards compatibility
  .confidence_raw   — 0–100 scale
  .confidence_state — logic state string
  .source_authority — SA value
  .temporal_factor  — TF value
  .corroboration_score — CC value
  .network_independence — NI value
  .claim_type       — "static" | "dynamic_high" | etc.
  .echo_chamber     — bool
  .decay_lambda     — λ value used
"""
from __future__ import annotations
import asyncio
import math
from dataclasses import dataclass
from src.verification.source_tagger import SourceTaggerAgent
from src.verification.temporal_agent import TemporalAgent
from src.verification.network_graph_agent import NetworkGraphAgent
from src.verification.adversarial_agent import AdversarialAgent
from src.verification.cross_referencer import CrossReferencer


# ── Logic state thresholds ───────────────────────────────────────────────────
VERIFIED_FACT_CS_FLOOR    = 65.0
BREAKING_CLAIM_CS_CEILING = 50.0
DEBUNK_AUTHORITY_FLOOR    = 0.80
DEBUNK_SCORE_FLOOR        = 0.55


@dataclass
class ScoringResult:
    """Full scoring output for a single claim."""
    claim_id: str
    cs: float                   # 0–100
    confidence: float           # 0.0–1.0 (cs/100)
    state: str                  # logic state
    sa: float                   # Source Authority
    tf: float                   # Temporal Factor
    cc: float                   # Corroboration Count
    ni: float                   # Network Independence
    claim_type: str             # "static" | "dynamic_high" | …
    echo_chamber: bool
    decay_lambda: float
    scoring_notes: list[str]    # per-agent reasoning


class ScoringOrchestrator:
    """
    Central coordinator for the multi-agent confidence scoring pipeline.

    Usage (sync entry point — wraps async internally):
        orchestrator = ScoringOrchestrator()
        orchestrator.score_all(ledger)   # mutates each claim in place

    Usage (async — preferred when inside an async context):
        await orchestrator.score_all_async(ledger)
    """

    def __init__(self):
        self.source_tagger  = SourceTaggerAgent()
        self.temporal_agent = TemporalAgent()
        self.network_agent  = NetworkGraphAgent()
        self.adversarial    = AdversarialAgent()

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def score_all(self, ledger) -> list[ScoringResult]:
        """
        Synchronous entry point — scores every claim in the ledger in place.
        Internally uses asyncio for Phase 1 parallelism.
        """
        # Step 1: Cross-reference (populates corroborating_claim_ids)
        # Must run before Phase 1 so NetworkGraphAgent sees the links
        CrossReferencer().cross_reference(ledger)

        # Step 2: Score each claim with the 4-agent pipeline
        results = []
        for claim in ledger.get_all_claims():
            result = self._score_one_sync(claim, ledger)
            self._apply_to_claim(claim, result)
            results.append(result)
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Internal scoring pipeline
    # ─────────────────────────────────────────────────────────────────────────

    def _score_one_sync(self, claim, ledger) -> ScoringResult:
        """Score a single claim — synchronous wrapper."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already inside an async context (e.g. FastAPI route)
                # Create a new event loop in a thread to avoid nesting
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(asyncio.run, self._score_one_async(claim, ledger))
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(self._score_one_async(claim, ledger))
        except Exception:
            return asyncio.run(self._score_one_async(claim, ledger))

    async def _score_one_async(self, claim, ledger) -> ScoringResult:
        """
        Full 4-agent pipeline for one claim.

        Phase 1: SourceTagger + Temporal + NetworkGraph run in parallel.
        Phase 2: Adversarial runs after (needs full network graph).
        """
        notes = []

        # ── Phase 1: Parallel agents ─────────────────────────────────────────
        # All three are synchronous internally but wrapped as coroutines
        # so asyncio.gather can schedule them concurrently
        source_profile, temporal_profile, network_profile = await asyncio.gather(
            asyncio.to_thread(self.source_tagger.tag, claim.source.source_url),
            asyncio.to_thread(self.temporal_agent.scope, claim),
            asyncio.to_thread(self.network_agent.analyse, claim, ledger),
        )

        notes.append(f"[SOURCE]  {'; '.join(source_profile.structural_notes)}")
        notes.append(f"[TEMPORAL] {temporal_profile.decay_notes}")
        notes.append(f"[NETWORK]  {network_profile.notes}")

        # ── Phase 2: Adversarial agent ────────────────────────────────────────
        adversarial_profile = await asyncio.to_thread(
            self.adversarial.scan, claim, ledger
        )
        notes.append(f"[ADVERSARIAL] {adversarial_profile.notes}")

        # ── Extract component scores ──────────────────────────────────────────
        sa = source_profile.authority
        tf = temporal_profile.temporal_factor
        cc = network_profile.cc
        ni = network_profile.ni

        # ── Geometric formula ─────────────────────────────────────────────────
        # CS = (SA × TF) × (CC × NI) × 100
        # Note: when CC=0 (sole source), the corroboration term becomes CC×NI=0
        # which would crater the score. Apply a minimum floor:
        #   If CC=0: use (SA × TF) × 0.30 as base (sole-source penalty)
        #   This gives a "prior" score based purely on source quality + recency
        if cc == 0.0:
            cs_raw = (sa * tf) * 0.30 * 100
            notes.append(
                f"[FORMULA] Sole-source floor applied: "
                f"CS = ({sa:.2f} × {tf:.3f}) × 0.30 × 100 = {cs_raw:.1f}"
            )
        else:
            cs_raw = (sa * tf) * (cc * ni) * 100
            notes.append(
                f"[FORMULA] CS = ({sa:.2f} × {tf:.3f}) × ({cc:.3f} × {ni:.3f}) × 100 = {cs_raw:.1f}"
            )

        cs = round(max(0.0, min(100.0, cs_raw)), 2)

        # ── Assign logic state ────────────────────────────────────────────────
        state = self._assign_state(
            cs=cs,
            cc=cc,
            adversarial=adversarial_profile,
            network=network_profile,
        )
        notes.append(f"[STATE] → {state}")

        return ScoringResult(
            claim_id=claim.claim_id,
            cs=cs,
            confidence=round(cs / 100.0, 4),
            state=state,
            sa=sa,
            tf=tf,
            cc=cc,
            ni=ni,
            claim_type=temporal_profile.claim_type,
            echo_chamber=network_profile.echo_chamber,
            decay_lambda=temporal_profile.decay_rate,
            scoring_notes=notes,
        )

    def _assign_state(self, cs: float, cc: float, adversarial, network) -> str:
        """
        Map scoring data to one of four logic states.

        Priority order (highest takes precedence):
          1. DEBUNKED          — high-authority counter-claim + high debunk_score
          2. ACTIVE_DISPUTE    — contradiction found but not definitively debunked
          3. VERIFIED_FACT     — CS ≥ threshold and no contradictions
          4. BREAKING_CLAIM    — low CS, no contradictions (sole/unverified source)
        """
        has_contradiction = adversarial.contradictions_found > 0
        is_debunked = (
            adversarial.is_actively_debunked
            and adversarial.max_counter_authority >= DEBUNK_AUTHORITY_FLOOR
            and adversarial.debunk_score >= DEBUNK_SCORE_FLOOR
        )

        if is_debunked:
            return "DEBUNKED"

        if has_contradiction:
            return "ACTIVE_DISPUTE"

        if cs >= VERIFIED_FACT_CS_FLOOR:
            return "VERIFIED_FACT"

        # Breaking claim: flag as "uncorroborated / sole claim"
        return "BREAKING_CLAIM"

    @staticmethod
    def _apply_to_claim(claim, result: ScoringResult):
        """
        Write ScoringResult back onto the Claim object in place.
        Updates both the old .confidence field (0–1) and new fields.
        """
        claim.confidence        = result.confidence       # 0.0–1.0 (backwards compat)
        claim.confidence_raw    = result.cs               # 0–100
        claim.confidence_state  = result.state
        claim.source_authority  = result.sa
        claim.temporal_factor   = result.tf
        claim.corroboration_score = result.cc
        claim.network_independence = result.ni
        claim.claim_type        = result.claim_type
        claim.echo_chamber      = result.echo_chamber
        claim.decay_lambda      = result.decay_lambda
        claim.scoring_notes     = result.scoring_notes
