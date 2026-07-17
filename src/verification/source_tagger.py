"""
source_tagger.py — Source Authority Agent
==========================================
Agent 1 of 4 in the multi-agent scoring pipeline.

Resolves domain structural metadata and assigns a Source Authority (SA) score.
SA is the "B" component from the old B.R.A.G system, rebuilt as a proper
tiered classifier with TLD-structural rules.

SA Range: 0.0 – 1.0
  Tier 1 (SA = 0.90): Government, edu, known global news agencies, OSINT DBs
  Tier 2 (SA = 0.65): Established regional press, Wikipedia, verified orgs
  Tier 3 (SA = 0.40): General blogs, smaller outlets, unknown .com/.org
  Tier 4 (SA = 0.15): Recently registered, unresolvable, social media handles
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from urllib.parse import urlparse
from src.config import SOURCE_RELIABILITY_TIERS


# Structural TLD rules — applied before whitelist lookup
# Any domain matching these TLDs gets an automatic minimum Tier 1 floor
GOV_TLDS = {".gov", ".mil", ".int"}
EDU_TLDS = {".edu", ".ac.uk", ".edu.au", ".ac.in"}

# Social media / UGC platforms — always Tier 4 ceiling
SOCIAL_PLATFORMS = {
    "twitter.com", "x.com", "facebook.com", "reddit.com",
    "tiktok.com", "instagram.com", "t.me", "telegram.org",
    "youtube.com",  # unless official channel — treated as low by default
}

# Regex for detecting "fresh domain" patterns (numeric/random prefixes, very short names)
SUSPICIOUS_DOMAIN_RE = re.compile(
    r'^(\d{4,}|[a-z]{2,4}\d{4,}|[a-z]-[a-z]-[a-z])\.'  # e.g. news2024.co, a-b-c.info
)


@dataclass
class SourceProfile:
    """Result returned by SourceTaggerAgent.tag()"""
    url: str
    domain: str
    tier: int               # 1–4
    authority: float        # SA score 0.0–1.0
    tld_rule: str           # How the tier was assigned
    structural_notes: list[str]  # Human-readable reasoning


class SourceTaggerAgent:
    """
    Resolves a source URL to a structured authority profile.

    Classification priority (highest wins):
      1. TLD structural rule (.gov/.mil/.edu → Tier 1)
      2. Social media ceiling (Tier 4)
      3. Whitelist lookup (Tier 1 or Tier 2)
      4. Suspicious domain heuristics (Tier 4)
      5. Default fallback (Tier 3)
    """

    def __init__(self):
        self.high_domains = set(SOURCE_RELIABILITY_TIERS["high"])
        self.medium_domains = set(SOURCE_RELIABILITY_TIERS["medium"])

    def tag(self, url: str) -> SourceProfile:
        """
        Classify a URL and return its SourceProfile.
        Synchronous — designed to be run inside asyncio.gather() alongside
        TemporalAgent and NetworkGraphAgent.
        """
        domain = self._extract_domain(url)
        notes = []

        # ── 1. TLD structural rule ───────────────────────────────────────────
        # .gov/.mil/.int are state-controlled — highest structural trust
        for tld in GOV_TLDS:
            if domain.endswith(tld):
                notes.append(f"Government TLD ({tld}) → automatic Tier 1")
                return SourceProfile(url=url, domain=domain, tier=1,
                                     authority=0.90, tld_rule=f"gov_tld:{tld}",
                                     structural_notes=notes)

        for tld in EDU_TLDS:
            if domain.endswith(tld):
                notes.append(f"Education TLD ({tld}) → Tier 1")
                return SourceProfile(url=url, domain=domain, tier=1,
                                     authority=0.85, tld_rule=f"edu_tld:{tld}",
                                     structural_notes=notes)

        # ── 2. Social media ceiling ──────────────────────────────────────────
        if any(s in domain for s in SOCIAL_PLATFORMS):
            notes.append("Social media / UGC platform → Tier 4 ceiling")
            return SourceProfile(url=url, domain=domain, tier=4,
                                 authority=0.15, tld_rule="social_platform",
                                 structural_notes=notes)

        # ── 3. Whitelist lookup ──────────────────────────────────────────────
        if any(d in domain for d in self.high_domains):
            notes.append("Matched high-authority whitelist (Tier 1)")
            return SourceProfile(url=url, domain=domain, tier=1,
                                 authority=0.90, tld_rule="whitelist_high",
                                 structural_notes=notes)

        if any(d in domain for d in self.medium_domains):
            notes.append("Matched medium-authority whitelist (Tier 2)")
            return SourceProfile(url=url, domain=domain, tier=2,
                                 authority=0.65, tld_rule="whitelist_medium",
                                 structural_notes=notes)

        # ── 4. Suspicious domain heuristics ─────────────────────────────────
        suspicion_score = self._suspicion_score(domain, url, notes)
        if suspicion_score >= 2:
            notes.append(f"Suspicion score {suspicion_score}/3 → Tier 4")
            return SourceProfile(url=url, domain=domain, tier=4,
                                 authority=max(0.15, 0.30 - suspicion_score * 0.05),
                                 tld_rule="suspicious_heuristic",
                                 structural_notes=notes)

        # ── 5. Default ───────────────────────────────────────────────────────
        notes.append("Unknown domain — default Tier 3")
        return SourceProfile(url=url, domain=domain, tier=3,
                             authority=0.40, tld_rule="default_tier3",
                             structural_notes=notes)

    def _extract_domain(self, url: str) -> str:
        """Parse netloc, strip www., lowercase."""
        try:
            netloc = urlparse(url).netloc.lower()
            return netloc.replace("www.", "").strip()
        except Exception:
            return url.lower()[:60]

    def _suspicion_score(self, domain: str, url: str, notes: list) -> int:
        """
        Heuristic suspicion scoring (0–3).
        Each flag adds 1 point. ≥2 → Tier 4.
        """
        score = 0

        # Flag 1: Domain matches suspicious regex pattern
        if SUSPICIOUS_DOMAIN_RE.search(domain):
            score += 1
            notes.append("Suspicious domain pattern (numeric/random prefix)")

        # Flag 2: Very short domain name (< 6 chars before TLD) — often spam
        name_part = domain.split(".")[0] if "." in domain else domain
        if len(name_part) < 5:
            score += 1
            notes.append(f"Short domain name '{name_part}' (< 5 chars)")

        # Flag 3: Unusual TLD — high-abuse registries
        HIGH_ABUSE_TLDS = {".xyz", ".top", ".click", ".tk", ".ml", ".ga", ".cf",
                           ".gq", ".info", ".biz", ".pw", ".cc"}
        for tld in HIGH_ABUSE_TLDS:
            if domain.endswith(tld):
                score += 1
                notes.append(f"High-abuse TLD ({tld})")
                break

        return score
