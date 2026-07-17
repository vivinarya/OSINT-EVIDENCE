import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.llm_client import LLMClient
from src.agent.react_loop import InvestigativeAgent

async def main():
    llm = LLMClient()
    print("Initializing agent...")
    agent = InvestigativeAgent(llm)
    
    print("Planning for 'hitler'...")
    plan = await agent.planner.plan("hitler")
    print("Plan generated:", plan)
    
    print("Executing plan...")
    results = await agent.executor.execute_plan(plan, parallel=True)
    print("Execution results completed. Number of results:", len(results))
    
    print("Reflecting...")
    evidence_summary = agent._summarize_evidence()
    print("Evidence summary:", evidence_summary)
    
    reflect = await agent.llm.generate_json(
        "You are an investigative agent. Here is your investigation question: hitler\n\n"
        f"Here is what you have learned so far:\n{evidence_summary}\n\n"
        "Do you have sufficient evidence to produce a complete report?\n"
        "- If YES, respond with: {\"decision\": \"report\", \"reasoning\": \"...\"}\n"
        "- If NO, respond with: {\"decision\": \"continue\", \"reasoning\": \"...\", \"follow_up\": \"specific follow-up question\"}"
    )
    print("Reflection decision:", reflect)
    
    print("Generating report...")
    report = await agent._generate_report("hitler")
    print("Report generated successfully! Report length:", len(report.get("report", "")))

if __name__ == "__main__":
    asyncio.run(main())
