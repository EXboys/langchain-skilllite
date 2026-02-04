"""
Basic usage example for langchain-skilllite with LangGraph agent.

This example shows how to:
1. Create a test skill dynamically
2. Load skills as LangChain tools
3. Use them with a LangGraph agent

Prerequisites:
    pip install langchain-skilllite langchain-openai langgraph

Usage:
    # Set your API key
    export OPENAI_API_KEY=your_key
    # Or use other providers like Qwen
    export BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
    export API_KEY=your_qwen_key

    python basic_usage.py
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_skilllite import SkillLiteToolkit, SkillLiteCallbackHandler
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


def create_calculator_skill(tmpdir: str) -> str:
    """Create a simple calculator skill for testing."""
    skill_dir = Path(tmpdir) / "calculator"
    skill_dir.mkdir()
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()

    # Create SKILL.md
    (skill_dir / "SKILL.md").write_text("""---
name: calculator
description: A calculator skill that performs basic arithmetic operations (add, subtract, multiply, divide).
license: MIT
metadata:
  author: example
  version: "1.0"
---

# Calculator Skill

Performs basic arithmetic operations on two numbers.
""")

    # Create main.py
    (scripts_dir / "main.py").write_text('''import sys
import json

def main(a: float, b: float, operation: str = "add") -> str:
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        result = a / b
    else:
        return f"Error: Unknown operation {operation}"
    return f"Result: {result}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
        print(main(float(params.get("a", 0)), float(params.get("b", 0)), params.get("operation", "add")))
''')
    return tmpdir


def main():
    # Check for API key
    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: No API key found!")
        print("   Set OPENAI_API_KEY or API_KEY environment variable")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        print("=" * 50)
        print("langchain-skilllite Basic Usage Example")
        print("=" * 50)

        # Create test skill
        print(f"\n📂 Creating test skill...")
        create_calculator_skill(tmpdir)

        # Load skills as LangChain tools
        tools = SkillLiteToolkit.from_directory(
            tmpdir,
            sandbox_level=1,  # Level 1 for quick testing (no sandbox)
        )

        print(f"\n✅ Loaded {len(tools)} tools:")
        for tool in tools:
            print(f"   • {tool.name}: {tool.description[:60]}...")

        # Create callback handler for monitoring
        callback_handler = SkillLiteCallbackHandler(verbose=True)

        # Configure LLM
        llm = ChatOpenAI(
            base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
            api_key=api_key,
            model=os.getenv("MODEL", "gpt-4"),
        )

        # Create agent with tools
        agent = create_react_agent(llm, tools)

        # Test the agent
        print("\n" + "=" * 50)
        print("Testing agent with calculator skill...")
        print("=" * 50)

        result = agent.invoke(
            {"messages": [("user", "Use the calculator to compute 15 + 27")]},
            config={"callbacks": [callback_handler]}
        )

        # Print result
        print("\n📤 Agent response:")
        for msg in result["messages"]:
            if hasattr(msg, "content") and msg.content:
                print(f"   [{msg.type}]: {msg.content[:200]}")

        # Print execution summary
        print("\n📊 Execution summary:")
        summary = callback_handler.get_execution_summary()
        print(f"   Total tool executions: {summary['tool_executions']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Errors: {summary['errors']}")


if __name__ == "__main__":
    main()
