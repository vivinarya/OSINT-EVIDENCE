import os
from dotenv import load_dotenv

load_dotenv()


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
OPENCORPORATES_API_KEY = os.getenv("OPENCORPORATES_API_KEY", "")
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")
GDELT_API_KEY = os.getenv("GDELT_API_KEY", "")

STEP_CAP = int(os.getenv("STEP_CAP", "15"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

LLM_PROVIDER = "gemini" if GEMINI_API_KEY else ("anthropic" if ANTHROPIC_API_KEY else "openai")

SOURCE_RELIABILITY_TIERS = {
    "high": [
        # US Government — primary sources
        "whitehouse.gov", "sec.gov", "treasury.gov", "congress.gov",
        "courts.gov", "justice.gov", "doj.gov", "fbi.gov", "cia.gov",
        "state.gov", "federalregister.gov", "archives.gov", "usa.gov",
        # OSINT / financial databases
        "opencorporates.com", "opensanctions.org", "icij.org",
        "gdeltproject.org", "ofac.treas.gov",
        # Tier-1 journalism (primary source / wire services)
        "reuters.com", "bloomberg.com", "ap.org", "apnews.com",
        "wsj.com", "ft.com",
    ],
    "medium": [
        # Reputable journalism
        "nytimes.com", "washingtonpost.com", "bbc.com", "bbc.co.uk",
        "theguardian.com", "economist.com", "cnbc.com",
        "forbes.com", "businessinsider.com",
        # Reference
        "wikipedia.org", "britannica.com",
        # Science
        "nature.com", "science.org",
    ],
    "low": [],  # everything else
}
