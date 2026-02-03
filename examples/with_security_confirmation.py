"""
Example with security confirmation callback (sandbox level 3).

This example demonstrates the FULL LangChain agent workflow with security scanning:
1. Load skills as LangChain tools with sandbox_level=3
2. Create a LangGraph agent with LLM
3. User asks to use a skill that contains potentially dangerous code
4. Security scan detects the issue and prompts for confirmation
5. User confirms or denies execution

Usage:
    # Set your API key first
    export OPENAI_API_KEY=your_key
    # Or for Qwen/other compatible APIs:
    export BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
    export API_KEY=your_key

    python with_security_confirmation.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_skilllite import SkillLiteToolkit, SkillLiteCallbackHandler
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


def confirmation_callback(security_report: str, scan_id: str) -> bool:
    """
    Callback function for security confirmation.

    This is called when a skill has high-severity security issues detected.
    The user must confirm before the skill can be executed.

    Args:
        security_report: Human-readable security report
        scan_id: Unique identifier for this scan

    Returns:
        True to proceed with execution, False to cancel
    """
    print("\n" + "=" * 60)
    print("🔒 SECURITY CONFIRMATION REQUIRED")
    print("=" * 60)
    print(security_report)
    print("=" * 60)

    response = input("\nProceed with execution? [y/N]: ").strip().lower()
    return response == 'y'


def main():
    skills_dir = os.path.join(os.path.dirname(__file__), "../../.skills")

    if not os.path.exists(skills_dir):
        print(f"Skills directory not found: {skills_dir}")
        return

    print("=" * 60)
    print("🔐 Security Confirmation Test (Full LLM Agent)")
    print("=" * 60)

    # Load skills with sandbox level 3 (security scanning + confirmation)
    print("\n📂 Loading skills with security scanning enabled...")
    tools = SkillLiteToolkit.from_directory(
        skills_dir,
        sandbox_level=3,  # Full security: sandbox + scanning
        confirmation_callback=confirmation_callback,
    )

    print(f"✅ Loaded {len(tools)} tools:")
    for tool in tools:
        print(f"   • {tool.name}")

    # Create callback handler for monitoring
    callback_handler = SkillLiteCallbackHandler(verbose=True)

    # Configure LLM
    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ Error: No API key found!")
        print("   Set OPENAI_API_KEY or API_KEY environment variable")
        return

    llm = ChatOpenAI(
        base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        model=os.getenv("MODEL", "gpt-4"),
    )

    # Create agent
    agent = create_react_agent(llm, tools)

    print("\n" + "-" * 60)
    print("Testing with file-helper skill...")
    print("This skill uses os.popen() which should trigger security scan!")
    print("-" * 60)

    # Use file-helper which looks harmless but contains os.popen()
    # The LLM should be willing to call this tool
    result = agent.invoke(
        {"messages": [("user", "请使用 file-helper 工具读取 /etc/hostname 文件的内容")]},
        config={"callbacks": [callback_handler]}
    )

    print("\n" + "=" * 60)
    print("Agent Response:")
    print("=" * 60)
    for msg in result["messages"]:
        if hasattr(msg, "content") and msg.content:
            print(f"  [{msg.type}]: {msg.content[:500]}")

    # Print execution summary
    print("\n" + "-" * 60)
    summary = callback_handler.get_execution_summary()
    print(f"📊 Execution Summary:")
    print(f"   Tool executions: {summary['tool_executions']}")
    print(f"   Successful: {summary['successful']}")
    print(f"   Errors: {summary['errors']}")


if __name__ == "__main__":
    main()

