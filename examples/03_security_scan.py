"""
Using security scanning with confirmation callback (sandbox level 3).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from langchain_skilllite import SkillLiteToolkit

# Load .env (from current working directory)
load_dotenv()

skills_dir = Path(".skills")
llm = ChatOpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
    model=os.getenv("MODEL", "gpt-4o-mini"),
)


# Define confirmation callback for user approval
def confirm_execution(report: str, scan_id: str) -> bool:
    """Ask user to confirm skill execution after security scan."""
    print("\n" + "=" * 60)
    print("🔐 SECURITY SCAN REPORT")
    print("=" * 60)
    print(report)
    print("=" * 60)
    response = input("\nProceed with execution? [y/N]: ").strip().lower()
    return response == 'y'


# Enable security scanning with confirmation callback
tools = SkillLiteToolkit.from_directory(
    skills_dir,
    sandbox_level=3,  # Enable security scanning
    force_confirmation=True,  # Always ask for confirmation
    confirmation_callback=confirm_execution,
)

agent = create_react_agent(llm, tools)
result = agent.invoke({"messages": [("user", "Echo 'test message'")]})

for msg in result["messages"]:
    print(f"[{msg.type}]: {msg.content[:200] if msg.content else ''}")

