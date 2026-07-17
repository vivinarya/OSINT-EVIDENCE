"""
adversarial_agent.py — Contradiction & Adversarial Agent
=========================================================
Agent 4 of 4 in the multi-agent scoring pipeline.

Runs AFTER the other 3 agents — it needs the full corroboration graph to be
built first. Its job is to actively search the ledger for counter-evidence
and assess whether this claim is being actively debunked.

Strategy: Semantic negation scanning
  1. Extract entity + action from the claim text.
  2. Scan all OTHER claims in the ledger for:
       - Direct negation keywords (denied, retracted, false, refuted)
       - Temporal override (a higher-authority source says the OPPOSITE)
       - Contradiction links already set by CrossReferencer
  3. Weight each contradiction by the counter-claim's source authority.
  4. Return an AdversarialProfile with debunk_score and logic_state hint.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse
from src.config import SOURCE_RELIABILITY_TIERS


# Keywords that signal a claim is being contradicted / retracted
NEGATION_SIGNALS = re.compile(
    r'\b(denied|denies|refuted|refutes|retracted|retraction|'
    r'false|debunked|misleading|misinformation|disinformation|'
    r'no evidence|did not|does not|was not|is not|'
    r'still (?:active|CEO|director|working|serving|alive)|'
    r'confirmed (?:not|false|incorrect|wrong)|'
    r'contradicts?|disputed?|challenged?|rejected?|dismissed?)\b',
    re.IGNORECASE,
)

# Keywords suggesting support/confirmation (used to avoid false positives)
SUPPORT_SIGNALS = re.compile(
    r'\b(confirmed|verified|corroborated|proven|established|'
    r'officially|acknowledged|admitted)\b',
    re.IGNORECASE,
)


@dataclass
class ContradictionEvidence:
    """A single piece of counter-evidence found against the target claim."""
    claim_id: str
    text: str
    source_url: str
    source_authority: float   # SA of the counter-claim's source
    negation_strength: float  # 0.0–1.0: how strong the negation signal is
    notes: str


@dataclass
class AdversarialProfile:
    """Result returned by AdversarialAgent.scan()"""
    contradictions_found: int
    max_counter_authority: float     # highest SA among counter-claims
    debunk_score: float              # 0.0–1.0 aggregate debunk pressure
    is_actively_debunked: bool       # True if high-authority counter-claim exists
    evidence: list[ContradictionEvidence]
    logic_state_hint: str            # "clean" | "disputed" | "debunked"
    notes: str


class AdversarialAgent:
    """
    Scans the evidence ledger for counter-evidence against a target claim.

    Run this AFTER CrossReferencer has linked claims — it uses both
    .contradicting_claim_ids (explicit links) and semantic negation scanning
    across all claims in the ledger.
    """

    def __init__(self):
        # Preload high-authority domains for counter-claim weighting
        self.high_domains = set(SOURCE_RELIABILITY_TIERS["high"])
        self.medium_domains = set(SOURCE_RELIABILITY_TIERS["medium"])

    def scan(self, claim, ledger) -> AdversarialProfile:
        """
        Scan for counter-evidence against `claim` across the full ledger.

        Parameters
        ----------
        claim  : Target Claim to defend/debunk
        ledger : Full EvidenceLedger (all other claims are candidates)
        """
        all_claims = ledger.get_all_claims()
        evidence: list[ContradictionEvidence] = []

        # ── Pass 1: Explicit contradiction links (from CrossReferencer) ──────
        for cid in claim.contradicting_claim_ids:
            counter = ledger.get_claim(cid)
            if counter:
                sa = self._source_authority(counter.source.source_url)
                evidence.append(ContradictionEvidence(
                    claim_id=cid,
                    text=counter.text,
                    source_url=counter.source.source_url,
                    source_authority=sa,
                    negation_strength=0.80,   # explicit link = strong signal
                    notes=f"Explicitly linked as contradiction by CrossReferencer. SA={sa:.2f}",
                ))

        # ── Pass 2: Semantic negation scan across full ledger ────────────────
        claim_words = set(claim.text.lower().split())
        for other in all_claims:
            if other.claim_id == claim.claim_id:
                continue
            if other.claim_id in claim.contradicting_claim_ids:
                continue  # already captured in Pass 1

            # Only consider claims with meaningful word overlap (shared subject)
            other_words = set(other.text.lower().split())
            overlap = len(claim_words & other_words)
            if overlap < 3:
                continue

            # Check for negation signals in the other claim
            if NEGATION_SIGNALS.search(other.text):
                # Avoid false positives: skip if it also has strong support signals
                # and the negation applies to something else
                has_support = bool(SUPPORT_SIGNALS.search(other.text))
                negation_strength = 0.60 if not has_support else 0.35
                sa = self._source_authority(other.source.source_url)
                evidence.append(ContradictionEvidence(
                    claim_id=other.claim_id,
                    text=other.text,
                    source_url=other.source.source_url,
                    source_authority=sa,
                    negation_strength=negation_strength,
                    notes=(
                        f"Semantic negation signal detected (word overlap={overlap}). "
                        f"SA={sa:.2f}, negation_strength={negation_strength:.2f}"
                    ),
                ))

        # ── Aggregate ────────────────────────────────────────────────────────
        if not evidence:
            return AdversarialProfile(
                contradictions_found=0,
                max_counter_authority=0.0,
                debunk_score=0.0,
                is_actively_debunked=False,
                evidence=[],
                logic_state_hint="clean",
                notes="No counter-evidence found in the ledger.",
            )

        max_sa = max(e.source_authority for e in evidence)
        # Debunk score: weighted sum of (SA × negation_strength), capped at 1.0
        debunk_score = min(
            sum(e.source_authority * e.negation_strength for e in evidence) / max(len(evidence), 1),
            1.0,
        )
        debunk_score = round(debunk_score, 4)

        # "Actively debunked" = at least one high-authority counter-claim
        is_debunked = max_sa >= 0.85 and debunk_score >= 0.60

        if is_debunked:
            logic_state_hint = "debunked"
            note = (
                f"⛔ DEBUNKED: {len(evidence)} counter-claim(s), highest SA={max_sa:.2f}, "
                f"debunk_score={debunk_score:.2f}. High-authority source contradicts this claim."
            )
        elif len(evidence) >= 2 or debunk_score >= 0.40:
            logic_state_hint = "disputed"
            note = (
                f"⚠ DISPUTED: {len(evidence)} counter-claim(s) found, "
                f"debunk_score={debunk_score:.2f}. Active disagreement in the evidence network."
            )
        else:
            logic_state_hint = "minor_conflict"
            note = (
                f"Minor conflict: {len(evidence)} weak counter-signal(s), "
                f"debunk_score={debunk_score:.2f}. Insufficient to downgrade claim state."
            )

        return AdversarialProfile(
            contradictions_found=len(evidence),
            max_counter_authority=max_sa,
            debunk_score=debunk_score,
            is_actively_debunked=is_debunked,
            evidence=evidence,
            logic_state_hint=logic_state_hint,
            notes=note,
        )

    def _source_authority(self, url: str) -> float:
        """Quick SA lookup — mirrors SourceTaggerAgent logic for counter-claims."""
        try:
            domain = urlparse(url).netloc.lower().replace("www.", "")
        except Exception:
            return 0.30
        # TLD structural check
        for gov_tld in (".gov", ".mil", ".int"):
            if domain.endswith(gov_tld):
                return 0.90
        for edu_tld in (".edu", ".ac.uk"):
            if domain.endswith(edu_tld):
                return 0.85
        if any(d in domain for d in self.high_domains):
            return 0.90
        if any(d in domain for d in self.medium_domains):
            return 0.65
        return 0.35
