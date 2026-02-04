"""
Example with security confirmation callback (sandbox level 3).

This example demonstrates the security scanning workflow:
1. Create a skill with potentially dangerous code (os.popen)
2. Load skills with sandbox_level=3 (security scanning enabled)
3. Security scan detects the issue and prompts for confirmation
4. User confirms or denies execution

Usage:
    # Set your API key first
    export OPENAI_API_KEY=your_key
    # Or for Qwen/other compatible APIs:
    export BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
    export API_KEY=your_key

    python with_security_confirmation.py
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_skilllite import SkillLiteToolkit, SkillLiteCallbackHandler
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


def create_dangerous_skill(tmpdir: str) -> str:
    """Create a skill with potentially dangerous code for security testing."""
    skill_dir = Path(tmpdir) / "file-reader"
    skill_dir.mkdir()
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()

    # Create SKILL.md
    (skill_dir / "SKILL.md").write_text("""---
name: file-reader
description: A file reader skill that reads file contents. WARNING - contains os.popen for testing security scanning.
license: MIT
metadata:
  author: example
  version: "1.0"
---

# File Reader Skill

Reads the contents of a file. This skill intentionally uses os.popen()
to demonstrate security scanning capabilities.
""")

    # Create main.py with dangerous code (os.popen)
    (scripts_dir / "main.py").write_text('''import sys
import json
import os

def main(filepath: str) -> str:
    """Read file contents using os.popen (dangerous!)."""
    try:
        # This is intentionally dangerous to trigger security scan
        result = os.popen(f"cat {filepath}").read()
        return f"File contents:\\n{result}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
        print(main(params.get("filepath", "")))
''')
    return tmpdir


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
    return response == "y"


def main():
    # Check for API key
    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: No API key found!")
        print("   Set OPENAI_API_KEY or API_KEY environment variable")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        print("=" * 60)
        print("🔐 Security Confirmation Example")
        print("=" * 60)

        # Create skill with dangerous code
        print("\n📂 Creating test skill with dangerous code (os.popen)...")
        create_dangerous_skill(tmpdir)

        # Load skills with sandbox level 3 (security scanning + confirmation)
        print("\n🔍 Loading skills with security scanning enabled...")
        tools = SkillLiteToolkit.from_directory(
            tmpdir,
            sandbox_level=3,  # Full security: sandbox + scanning
            confirmation_callback=confirmation_callback,
        )

        print(f"\n✅ Loaded {len(tools)} tools:")
        for tool in tools:
            print(f"   • {tool.name}")

        # Create callback handler for monitoring
        callback_handler = SkillLiteCallbackHandler(verbose=True)

        # Configure LLM
        llm = ChatOpenAI(
            base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
            api_key=api_key,
            model=os.getenv("MODEL", "gpt-4"),
        )

        # Create agent
        agent = create_react_agent(llm, tools)

        print("\n" + "-" * 60)
        print("Testing with file-reader skill...")
        print("This skill uses os.popen() which should trigger security scan!")
        print("-" * 60)

        result = agent.invoke(
            {"messages": [("user", "Use the file-reader to read /etc/hostname")]},
            config={"callbacks": [callback_handler]},
        )

        print("\n" + "=" * 60)
        print("📤 Agent Response:")
        print("=" * 60)
        for msg in result["messages"]:
            if hasattr(msg, "content") and msg.content:
                print(f"   [{msg.type}]: {msg.content[:500]}")

        # Print execution summary
        print("\n" + "-" * 60)
        summary = callback_handler.get_execution_summary()
        print(f"📊 Execution Summary:")
        print(f"   Tool executions: {summary['tool_executions']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Errors: {summary['errors']}")


if __name__ == "__main__":
    main()
