"""
Using callbacks to track tool execution.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from langchain_skilllite import SkillLiteToolkit, SkillLiteCallbackHandler

# Load .env (from current working directory)
load_dotenv()

skills_dir = Path(".skills")
llm = ChatOpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
    model=os.getenv("MODEL", "gpt-4o-mini"),
)

tools = SkillLiteToolkit.from_directory(skills_dir)

# Create callback handler
callback = SkillLiteCallbackHandler()

agent = create_react_agent(llm, tools)
result = agent.invoke(
    {"messages": [("user", "Greet Alice")]},
    config={"callbacks": [callback]}
)

# Show execution stats
summary = callback.get_execution_summary()
print(f"\nExecutions: {summary['tool_executions']}")
print(f"Successful: {summary['successful']}")

