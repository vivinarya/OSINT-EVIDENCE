"""
temporal_agent.py — Temporal Scoping Agent
===========================================
Agent 2 of 4 in the multi-agent scoring pipeline.

Classifies a claim as Static or Dynamic, then computes the Temporal Factor (TF).

Static claims (historical facts, birthdates, founding dates):
  TF = 1.0  — truth doesn't decay over time

Dynamic claims (current roles, breaking news, live prices):
  TF = e^(-λ · t)
  where:
    λ = decay rate constant (higher = faster decay)
    t = elapsed time in appropriate units (hours for breaking, days for roles)

Decay Levels:
  HIGH   (λ=0.50, t=hours): Breaking news, "resigned last night", "announced today"
  MEDIUM (λ=0.05, t=days):  Corporate roles, "currently CEO of", market positions
  LOW    (λ=0.001, t=days): Annual reports, regulatory filings, legal status
"""
from __future__ import annotations
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone


# ── Keyword classifiers ──────────────────────────────────────────────────────

# If ANY of these match → claim is STATIC, TF = 1.0
STATIC_KEYWORDS = re.compile(
    r'\b(born in|founded in|incorporated in|established in|'
    r'died in|graduated|served as|was the \d+|is the \d+|'
    r'historically|in \d{4}|since \d{4}|as of \d{4}|'
    r'year-old|years ago|decades ago|century|'
    r'is an American|is a former|was a|were a)\b',
    re.IGNORECASE,
)

# HIGH-decay dynamic signals — breaking/real-time events
HIGH_DECAY_KEYWORDS = re.compile(
    r'\b(last night|last hour|this morning|just now|breaking|'
    r'today|tonight|hours ago|minutes ago|'
    r'resigned|fired|arrested|charged|indicted|'
    r'announced|declared|confirmed|revealed|'
    r'crashed|surged|spiked|plummeted|halted)\b',
    re.IGNORECASE,
)

# MEDIUM-decay dynamic signals — current state claims
MEDIUM_DECAY_KEYWORDS = re.compile(
    r'\b(currently|now|is the CEO|is the director|is the president|'
    r'is running|is leading|serves as|holds the position|'
    r'this year|this month|this quarter|'
    r'recently|latest|new|ongoing|active|pending)\b',
    re.IGNORECASE,
)

# LOW-decay dynamic — semi-stable institutional claims
LOW_DECAY_KEYWORDS = re.compile(
    r'\b(annual report|regulatory filing|registered|incorporated|'
    r'listed on|stock exchange|subsidiary|division of|'
    r'headquartered in|based in|operates in)\b',
    re.IGNORECASE,
)

# Decay constants (λ)
LAMBDA = {
    "high":   0.50,   # t in hours  — validity window: ~2h half-life
    "medium": 0.05,   # t in days   — validity window: ~14d half-life
    "low":    0.001,  # t in days   — validity window: ~693d (~2yr) half-life
}


@dataclass
class TemporalProfile:
    """Result returned by TemporalAgent.scope()"""
    claim_type: str         # "static" | "dynamic_high" | "dynamic_medium" | "dynamic_low"
    decay_rate: float       # λ value used
    temporal_factor: float  # TF in [0.0, 1.0]
    elapsed: float          # t value used (hours or days depending on level)
    decay_notes: str        # Human-readable explanation


class TemporalAgent:
    """
    Classifies a claim's temporal nature and computes TF = e^(-λ·t).

    Usage:
        profile = TemporalAgent().scope(claim)
        tf = profile.temporal_factor
    """

    def scope(self, claim) -> TemporalProfile:
        """
        Analyse claim text + timestamp to produce a TemporalProfile.

        Parameters
        ----------
        claim : Claim object with .text and .timestamp attributes
        """
        text = claim.text or ""
        timestamp = claim.timestamp or ""
        elapsed_hours = self._elapsed_hours(timestamp)
        elapsed_days = elapsed_hours / 24.0

        # ── Static check first ───────────────────────────────────────────────
        if STATIC_KEYWORDS.search(text):
            return TemporalProfile(
                claim_type="static",
                decay_rate=0.0,
                temporal_factor=1.0,
                elapsed=0.0,
                decay_notes=(
                    f"Static claim detected (historical/biographical keywords). "
                    f"TF locked to 1.0 — truth doesn't decay over time."
                ),
            )

        # ── HIGH decay: breaking news / real-time events ─────────────────────
        if HIGH_DECAY_KEYWORDS.search(text):
            lam = LAMBDA["high"]
            t = elapsed_hours
            tf = self._decay(lam, t)
            return TemporalProfile(
                claim_type="dynamic_high",
                decay_rate=lam,
                temporal_factor=tf,
                elapsed=t,
                decay_notes=(
                    f"HIGH-decay dynamic claim (breaking news keywords). "
                    f"λ={lam}, t={t:.1f}h elapsed → TF={tf:.3f}. "
                    f"Half-life ≈ {0.693/lam:.1f}h. "
                    f"{'⚠ Requires immediate corroboration.' if tf < 0.5 else ''}"
                ),
            )

        # ── MEDIUM decay: current-state claims ───────────────────────────────
        if MEDIUM_DECAY_KEYWORDS.search(text):
            lam = LAMBDA["medium"]
            t = elapsed_days
            tf = self._decay(lam, t)
            return TemporalProfile(
                claim_type="dynamic_medium",
                decay_rate=lam,
                temporal_factor=tf,
                elapsed=t,
                decay_notes=(
                    f"MEDIUM-decay dynamic claim (current-role keywords). "
                    f"λ={lam}, t={t:.1f}d elapsed → TF={tf:.3f}. "
                    f"Half-life ≈ {0.693/lam:.0f}d."
                ),
            )

        # ── LOW decay: institutional / regulatory ────────────────────────────
        if LOW_DECAY_KEYWORDS.search(text):
            lam = LAMBDA["low"]
            t = elapsed_days
            tf = self._decay(lam, t)
            return TemporalProfile(
                claim_type="dynamic_low",
                decay_rate=lam,
                temporal_factor=tf,
                elapsed=t,
                decay_notes=(
                    f"LOW-decay institutional claim. "
                    f"λ={lam}, t={t:.0f}d elapsed → TF={tf:.3f}. "
                    f"Half-life ≈ {0.693/lam:.0f}d."
                ),
            )

        # ── Default: treat freshly retrieved claims as medium-decay ──────────
        lam = LAMBDA["medium"]
        t = elapsed_days
        tf = self._decay(lam, t)
        return TemporalProfile(
            claim_type="dynamic_medium",
            decay_rate=lam,
            temporal_factor=tf,
            elapsed=t,
            decay_notes=(
                f"No static/dynamic keywords detected — defaulting to MEDIUM decay. "
                f"λ={lam}, t={t:.1f}d → TF={tf:.3f}."
            ),
        )

    @staticmethod
    def _decay(lam: float, t: float) -> float:
        """TF = e^(-λ·t), clamped to [0.05, 1.0]"""
        if lam == 0.0 or t <= 0:
            return 1.0
        return round(max(0.05, min(1.0, math.exp(-lam * t))), 4)

    @staticmethod
    def _elapsed_hours(timestamp_str: str) -> float:
        """Parse ISO-8601 timestamp and return hours elapsed since now."""
        try:
            claim_time = datetime.fromisoformat(timestamp_str)
            if claim_time.tzinfo is None:
                claim_time = claim_time.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - claim_time
            return max(0.0, delta.total_seconds() / 3600.0)
        except (ValueError, TypeError):
            return 0.0  # unknown → treat as just-retrieved (TF ≈ 1.0)
