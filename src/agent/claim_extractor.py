from __future__ import annotations
import re
from src.llm_client import LLMClient


SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')
SKIP_PATTERNS = re.compile(
    r'^(link|image|photo|credit|subscribe|sign up|click|read more|'
    r'copyright|disclaimer|privacy|terms of service|advertisement|'
    r'powered by|all rights reserved|cookie|feedback|share|tweet|'
    r'follow us|contact us|search results|skip to|menu|navigation)',
    re.IGNORECASE,
)
VALUABLE_PATTERNS = re.compile(
    r'(was founded|founded in|incorporated|based in|headquartered|'
    r'registered in|owned by|subsidiary of|director|officer|'
    r'\$\d+|\d+ million|\d+ billion|\d+%|established|'
    r'charged|convicted|sentenced|investigated|fined|penalty|'
    r'shell company|offshore|tax haven|Panama Papers|'
    r'sanctions|OFAC|blocked|embargo|restricted|'
    r'conflict|violence|protest|riot|clash|attack|casualty|'
    r'president|prime minister|politician|congress|senator|'
    r'governor|mayor|ambassador|candidate|elected|appointed|'
    r'CEO|chairman|executive|founder|co-founder|'
    r'impeached|indicted|acquitted|testified|'
    r'born in|died in|graduated|served as|known for|'
    r'is an American|is a former|was the \d+|is the \d+)',
    re.IGNORECASE,
)


class ClaimExtractor:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def extract(self, content: str, source_type: str = "web") -> list[dict]:
        if not content or len(content.strip()) < 20:
            return []
        lines = content.split("\n")
        claims = []
        seen = set()
        for line in lines:
            line = line.strip()
            if not line or len(line) < 30:
                continue
            sentences = SENTENCE_SPLIT.split(line)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20 or len(sentence) > 500:
                    continue
                if SKIP_PATTERNS.search(sentence):
                    continue
                is_valuable = bool(VALUABLE_PATTERNS.search(sentence))
                if is_valuable or (len(sentence) > 50 and sentence[0].isupper()):
                    normalized = sentence.lower()[:100]
                    if normalized not in seen:
                        seen.add(normalized)
                        claims.append({
                            "text": sentence[:300],
                            "confidence": 0.65 if is_valuable else 0.5,
                            "source_type": source_type,
                        })
        return claims[:15]
