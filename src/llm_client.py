from __future__ import annotations
import json
import re
from src.config import LLM_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


class LLMClient:
    def __init__(self):
        self.provider = LLM_PROVIDER

    async def generate_json(self, prompt: str) -> dict | list:
        text = await self._generate_text(prompt, max_tokens=4096)
        return self._parse_json(text)

    async def generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        return await self._generate_text(prompt, max_tokens)

    async def _generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        if self.provider == "anthropic":
            return await self._anthropic_call(prompt, max_tokens)
        return await self._openai_call(prompt, max_tokens)

    async def _anthropic_call(self, prompt: str, max_tokens: int) -> str:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except ImportError:
            return await self._openai_call(prompt, max_tokens)
        except Exception as e:
            return f"Error: {e}"

    async def _openai_call(self, prompt: str, max_tokens: int) -> str:
        try:
            from openai import AsyncOpenAI
            kwargs = {"api_key": OPENAI_API_KEY or "sk-dummy"}
            if OPENAI_BASE_URL:
                kwargs["base_url"] = OPENAI_BASE_URL
            client = AsyncOpenAI(**kwargs)
            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error: {e}"

    def _parse_json(self, text: str) -> dict | list:
        text = text.strip()
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            text = json_match.group(1).strip()
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if json_match:
            text = json_match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        try:
            text = re.sub(r',\s*([}\]])', r'\1', text)
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text[:1000], "parse_error": True}
