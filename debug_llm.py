import asyncio
import sys
import os
from openai import AsyncOpenAI

sys.path.insert(0, os.path.dirname(__file__))

from src.agent.planner import PLANNER_PROMPT
from src.config import OPENAI_API_KEY, OPENAI_BASE_URL

async def test_model(model_name: str):
    print(f"\n--- Testing model: {model_name} ---")
    kwargs = {"api_key": OPENAI_API_KEY or "sk-dummy"}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    client = AsyncOpenAI(**kwargs)
    
    prompt = PLANNER_PROMPT.format(query="hitler")
    
    import time
    start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0
        )
        duration = time.time() - start
        print(f"Success in {duration:.2f} seconds!")
        text = response.choices[0].message.content or ""
        print("Response length:", len(text))
        print("Preview:")
        print(text[:300])
    except Exception as e:
        print("Error:", e)

async def main():
    models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-2-9b-it:free",
        "qwen/qwen3-coder:free"
    ]
    for model in models:
        await test_model(model)

if __name__ == "__main__":
    asyncio.run(main())
