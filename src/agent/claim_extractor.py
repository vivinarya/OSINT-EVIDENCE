from __future__ import annotations
import re
from src.llm_client import LLMClient


SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')
VALUABLE_PATTERNS = re.compile(
    r'(was founded|incorporated|based in|headquartered|sanctioned|listed on|'
    r'registered in|owned by|subsidiary of|director|officer|'
    r'\$\d+|\d+ million|\d+ billion|\d+%|founded in|established|'
    r'charged|convicted|sentenced|investigated|fined|penalty|'
    r'shell company|offshore|tax haven|Panama Papers|'
    r'sanctions|OFAC|blocked|embargo|restricted|'
    r'conflict|violence|protest|riot|clash|attack|casualty)',
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
                if VALUABLE_PATTERNS.search(sentence):
                    normalized = sentence.lower()[:100]
                    if normalized not in seen:
                        seen.add(normalized)
                        claims.append({
                            "text": sentence,
                            "confidence": 0.6,
                            "source_type": source_type,
                        })
        return claims[:15]
