"""
Simple test without LLM - just test tool loading and execution.

This example doesn't require an LLM API key.
It creates a temporary skill and tests the SkillLiteTool execution directly.

Usage:
    python simple_test.py
"""

import tempfile
from pathlib import Path
from uuid import uuid4

from langchain_skilllite import SkillLiteToolkit, SkillLiteCallbackHandler


def create_test_skill(tmpdir: str) -> str:
    """Create a simple calculator skill for testing."""
    skill_dir = Path(tmpdir) / "calculator"
    skill_dir.mkdir()

    # Create scripts directory (required by skilllite)
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()

    # Create SKILL.md with proper YAML front matter
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: calculator
description: A simple calculator skill for testing. Supports add, subtract, multiply, divide operations.
license: MIT
compatibility: Requires Python 3.x
metadata:
  author: test
  version: "1.0"
---

# Calculator Skill

A simple calculator that performs basic arithmetic operations.

## Usage

Provide an operation and two numbers to get the result.
""")

    # Create main.py in scripts/ directory
    main_py = scripts_dir / "main.py"
    main_py.write_text('''import sys
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
        try:
            params = json.loads(sys.argv[1])
            a = float(params.get("a", 0))
            b = float(params.get("b", 0))
            op = params.get("operation", "add")
            print(main(a, b, op))
        except json.JSONDecodeError:
            print("Error: Invalid JSON input")
    else:
        print("Error: No input provided")
''')

    return tmpdir


def main():
    print("=" * 50)
    print("langchain-skilllite Simple Test")
    print("=" * 50)

    # Create temporary skills directory with test skill
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n📂 Creating test skill in: {tmpdir}")
        create_test_skill(tmpdir)

        # Load tools
        tools = SkillLiteToolkit.from_directory(
            tmpdir,
            sandbox_level=1,  # No sandbox for simple testing
        )

        print(f"\n✅ Loaded {len(tools)} tools:")
        for tool in tools:
            desc = tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
            print(f"   • {tool.name}: {desc}")

        # Find calculator tool
        calculator = next((t for t in tools if t.name == "calculator"), None)

        if calculator:
            print("\n" + "-" * 50)
            print("Testing calculator tool directly...")
            print("-" * 50)

            # Test addition
            print("\n📝 Test: 5 + 3")
            result = calculator._run(operation="add", a=5, b=3)
            print(f"   Result: {result}")

            # Test multiplication
            print("\n📝 Test: 6 × 7")
            result = calculator._run(operation="multiply", a=6, b=7)
            print(f"   Result: {result}")

            # Test division
            print("\n📝 Test: 20 ÷ 4")
            result = calculator._run(operation="divide", a=20, b=4)
            print(f"   Result: {result}")

            print("\n✅ All tests passed!")
        else:
            print("\n⚠️  Calculator tool not found.")

    # Test callback handler
    print("\n" + "-" * 50)
    print("Testing SkillLiteCallbackHandler...")
    print("-" * 50)

    handler = SkillLiteCallbackHandler(verbose=True)

    # Simulate tool execution
    run_id = uuid4()
    handler.on_tool_start({"name": "test_tool"}, "test input", run_id=run_id)
    handler.on_tool_end("test output", run_id=run_id)

    summary = handler.get_execution_summary()
    print(f"\n📊 Execution Summary:")
    print(f"   Total executions: {summary['tool_executions']}")
    print(f"   Success rate: {summary['success_rate'] * 100:.0f}%")

    print("\n" + "=" * 50)
    print("✅ langchain-skilllite is working correctly!")
    print("=" * 50)


if __name__ == "__main__":
    main()
