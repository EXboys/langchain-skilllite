"""
Basic usage: Load skills and use with LangChain agent.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from langchain_skilllite import SkillLiteToolkit

# Load .env (from current working directory)
load_dotenv()

# Setup
skills_dir = Path(".skills")
llm = ChatOpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
    model=os.getenv("MODEL", "gpt-4o-mini"),
)

# Load skills as LangChain tools
tools = SkillLiteToolkit.from_directory(skills_dir)

print(f"Loaded {len(tools)} skills: {[t.name for t in tools]}")

# Create agent and run
agent = create_react_agent(llm, tools)
result = agent.invoke({"messages": [("user", "Convert 'hello world' to uppercase")]})

# Print result
for msg in result["messages"]:
    print(f"[{msg.type}]: {msg.content[:200] if msg.content else ''}")

