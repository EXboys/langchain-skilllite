"""
Basic usage example for langchain-skilllite.

This example shows how to:
1. Load skills from a directory as LangChain tools
2. Use them with a LangGraph agent

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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import langchain-skilllite
from langchain_skilllite import SkillLiteToolkit, SkillLiteCallbackHandler

# Import LangChain components
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


def main():
    # Path to skills directory (adjust as needed)
    skills_dir = os.path.join(os.path.dirname(__file__), "../../.skills")
    
    if not os.path.exists(skills_dir):
        print(f"Skills directory not found: {skills_dir}")
        print("Please adjust the skills_dir path or create some skills.")
        return
    
    # Load all skills as LangChain tools
    print("Loading skills from:", skills_dir)
    tools = SkillLiteToolkit.from_directory(
        skills_dir,
        sandbox_level=1,  # Level 1 for quick testing (no sandbox)
    )
    
    print(f"Loaded {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")
    
    # Create callback handler for monitoring
    callback_handler = SkillLiteCallbackHandler(verbose=True)
    
    # Configure LLM (OpenAI or compatible API)
    llm = ChatOpenAI(
        base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY"),
        model=os.getenv("MODEL", "gpt-4"),
    )
    
    # Create agent with tools
    agent = create_react_agent(llm, tools)
    
    # Test the agent
    print("\n" + "=" * 50)
    print("Testing agent with calculator skill...")
    print("=" * 50)
    
    result = agent.invoke(
        {"messages": [("user", "使用 calculator 技能计算 15 + 27")]},
        config={"callbacks": [callback_handler]}
    )
    
    # Print result
    print("\nAgent response:")
    for msg in result["messages"]:
        if hasattr(msg, "content") and msg.content:
            print(f"  {msg.type}: {msg.content[:200]}")
    
    # Print execution summary
    print("\nExecution summary:")
    summary = callback_handler.get_execution_summary()
    print(f"  Total tool executions: {summary['tool_executions']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Errors: {summary['errors']}")


if __name__ == "__main__":
    main()

