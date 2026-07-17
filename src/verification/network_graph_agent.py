"""
network_graph_agent.py — Network Graph Agent
=============================================
Agent 3 of 4 in the multi-agent scoring pipeline.

Analyses the web of corroborating claims to compute two metrics:

  CC — Corroboration Count (0.0–1.0)
       Normalised count of independent sources that agree with this claim.
       5+ unique corroborators → CC = 1.0

  NI — Network Independence (0.0–1.0)
       Ratio of distinct domain families among corroborators.
       Detects echo chambers: if 5 claims all come from the same parent domain,
       NI stays low (≈0.2) even though CC would look high.

Echo Chamber Detection:
  Groups domains by their "family" — the registrable domain (TLD+1).
  e.g. blog.newscorp.com, opinion.newscorp.com, sports.newscorp.com
  all belong to family "newscorp.com" → counted as ONE independent source.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from urllib.parse import urlparse
from collections import defaultdict


# CC normalisation: how many corroborators = full corroboration score
CC_SATURATION = 5   # 5+ unique sources → CC = 1.0

# Minimum NI when corroborators exist but ALL come from same domain family
NI_ECHO_FLOOR = 0.10


@dataclass
class DomainCluster:
    """One group of sources sharing the same domain family."""
    family: str              # registrable domain, e.g. "nytimes.com"
    domains: list[str]       # all subdomains seen, e.g. ["www.nytimes.com", "opinion.nytimes.com"]
    claim_ids: list[str]     # claim IDs belonging to this cluster
    authority: float = 0.0   # max SA from claims in this cluster (filled by orchestrator)


@dataclass
class NetworkProfile:
    """Result returned by NetworkGraphAgent.analyse()"""
    cc: float                       # Corroboration Count 0.0–1.0
    ni: float                       # Network Independence 0.0–1.0
    echo_chamber: bool              # True if corroborators are dominated by 1 family
    unique_corroborators: int       # count of truly independent domain families
    total_corroborators: int        # raw count of corroborating claims
    domain_clusters: list[DomainCluster]  # structured graph of corroborating sources
    notes: str                      # human-readable summary


class NetworkGraphAgent:
    """
    Analyses corroboration links for a claim and builds a domain network graph.

    Algorithm:
      1. Collect all corroborating claims from the ledger.
      2. Extract and normalise each source URL to its "domain family" (TLD+1).
      3. Group claims by domain family → DomainClusters.
      4. CC = min(unique_families / CC_SATURATION, 1.0)
      5. NI = unique_families / max(total_corroborators, 1)
         — penalises echo chambers where many claims come from 1 family.
      6. Echo chamber flag: if NI < 0.30 and total_corroborators >= 2.
    """

    def analyse(self, claim, ledger) -> NetworkProfile:
        """
        Build the network graph for a single claim.

        Parameters
        ----------
        claim  : Claim with .corroborating_claim_ids populated
        ledger : EvidenceLedger to look up corroborating claim objects
        """
        corroborating_claims = [
            ledger.get_claim(cid)
            for cid in claim.corroborating_claim_ids
            if ledger.get_claim(cid)
        ]

        # Also include the claim's own source in the network
        all_sources = [(claim.source.source_url, claim.claim_id)]
        for c in corroborating_claims:
            all_sources.append((c.source.source_url, c.claim_id))

        # ── Build domain family clusters ─────────────────────────────────────
        family_map: dict[str, DomainCluster] = {}
        for url, cid in all_sources:
            full_domain = self._extract_domain(url)
            family = self._domain_family(full_domain)
            if family not in family_map:
                family_map[family] = DomainCluster(
                    family=family, domains=[], claim_ids=[]
                )
            if full_domain not in family_map[family].domains:
                family_map[family].domains.append(full_domain)
            if cid not in family_map[family].claim_ids:
                family_map[family].claim_ids.append(cid)

        total_corroborators = len(corroborating_claims)
        # Subtract 1 for the claim's own family if it's the only member
        unique_families = len(family_map)

        # ── Compute CC ───────────────────────────────────────────────────────
        # Use unique domain families (not raw count) to avoid echo chamber inflation
        # Subtract 1 because the claim's own domain is always in the map
        independent_families = max(0, unique_families - 1)
        cc = round(min(independent_families / CC_SATURATION, 1.0), 4)

        # ── Compute NI ───────────────────────────────────────────────────────
        if total_corroborators == 0:
            ni = 0.40   # sole source — partial independence floor
            echo = False
        else:
            ni = round(independent_families / max(total_corroborators, 1), 4)
            ni = max(NI_ECHO_FLOOR, min(ni, 1.0))
            echo = ni < 0.30 and total_corroborators >= 2

        # ── Build notes ──────────────────────────────────────────────────────
        if total_corroborators == 0:
            notes = "No corroborators — sole-source claim. CC=0.0, NI=0.40 (floor)."
        elif echo:
            families_str = ", ".join(list(family_map.keys())[:5])
            notes = (
                f"⚠ ECHO CHAMBER DETECTED: {total_corroborators} corroborators "
                f"from only {independent_families} distinct domain famil{'y' if independent_families==1 else 'ies'} "
                f"({families_str}). NI={ni:.2f} penalised."
            )
        else:
            notes = (
                f"{total_corroborators} corroborators across {independent_families} "
                f"independent domain famil{'y' if independent_families==1 else 'ies'}. "
                f"CC={cc:.2f}, NI={ni:.2f}."
            )

        return NetworkProfile(
            cc=cc,
            ni=ni,
            echo_chamber=echo,
            unique_corroborators=independent_families,
            total_corroborators=total_corroborators,
            domain_clusters=list(family_map.values()),
            notes=notes,
        )

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Parse netloc and strip www."""
        try:
            netloc = urlparse(url).netloc.lower()
            return netloc.replace("www.", "").strip()
        except Exception:
            return url[:60].lower()

    @staticmethod
    def _domain_family(domain: str) -> str:
        """
        Extract the registrable domain (TLD+1 label).
        e.g. "opinion.nytimes.com" → "nytimes.com"
             "data.police.uk"       → "police.uk"
             "whitehouse.gov"       → "whitehouse.gov"

        This groups subdomains together so a media company with 10 blogs
        on *.newscorp.com only counts as ONE independent source.
        """
        parts = domain.split(".")
        if len(parts) >= 3:
            # Handle known 2-part TLDs: .co.uk, .com.au, .gov.uk, .ac.uk…
            two_part_tlds = {
                "co.uk", "com.au", "co.nz", "co.in", "gov.uk",
                "ac.uk", "org.uk", "net.au", "com.br", "co.za"
            }
            suffix = ".".join(parts[-2:])
            if suffix in two_part_tlds and len(parts) >= 3:
                return ".".join(parts[-3:])
            return ".".join(parts[-2:])
        return domain
