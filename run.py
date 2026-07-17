import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


def cli_mode(query: str):
    import asyncio
    from src.llm_client import LLMClient
    from src.agent.react_loop import InvestigativeAgent
    from src.reporting import ReportGenerator

    async def run():
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        llm = LLMClient()
        agent = InvestigativeAgent(llm)
        result = await agent.investigate(query)
        gen = ReportGenerator(llm)
        report = gen.generate(result["ledger"], query)
        print(report)

    asyncio.run(run())


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--cli":
        cli_mode(" ".join(sys.argv[2:]))
    else:
        from src.ui.app import *
        import subprocess
        subprocess.run(["streamlit", "run", os.path.join(os.path.dirname(__file__), "src", "ui", "app.py")])
