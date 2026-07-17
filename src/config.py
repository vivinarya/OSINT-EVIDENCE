import os
from dotenv import load_dotenv

load_dotenv()


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
OPENCORPORATES_API_KEY = os.getenv("OPENCORPORATES_API_KEY", "")
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")
GDELT_API_KEY = os.getenv("GDELT_API_KEY", "")

STEP_CAP = int(os.getenv("STEP_CAP", "15"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "fc-91d975f50e294bcf9cca7c00c7461f8b")

LLM_PROVIDER = "anthropic" if ANTHROPIC_API_KEY else "openai"

SOURCE_RELIABILITY_TIERS = {
    "high": [
        "sec.gov", "opencorporates.com", "opensanctions.org",
        "treasury.gov", "icij.org", "congress.gov", "courts.gov",
        "gdeltproject.org", "reuters.com", "bloomberg.com",
        "wsj.com", "ft.com", "ap.org", "reuters.com",
    ],
    "medium": [
        "nytimes.com", "washingtonpost.com", "bbc.com",
        "theguardian.com", "economist.com", "nature.com",
        "science.org", "cnbc.com", "forbes.com", "businessinsider.com",
    ],
    "low": [],  # everything else
}
