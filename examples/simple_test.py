"""
Simple test without LLM - just test tool loading and execution.

This example doesn't require an LLM API key.
It directly tests the SkillLiteTool execution.

Usage:
    python simple_test.py
"""

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_skilllite import SkillLiteToolkit, SkillLiteCallbackHandler


def main():
    # Path to skills directory
    skills_dir = os.path.join(os.path.dirname(__file__), "../../.skills")
    
    if not os.path.exists(skills_dir):
        print(f"❌ Skills directory not found: {skills_dir}")
        print("Please adjust the skills_dir path.")
        return
    
    print("=" * 50)
    print("langchain-skilllite Simple Test")
    print("=" * 50)
    
    # Load tools
    print(f"\n📂 Loading skills from: {skills_dir}")
    tools = SkillLiteToolkit.from_directory(
        skills_dir,
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
        print("\n⚠️  Calculator tool not found. Available tools:")
        for tool in tools:
            print(f"   - {tool.name}")
    
    # Test callback handler
    print("\n" + "-" * 50)
    print("Testing SkillLiteCallbackHandler...")
    print("-" * 50)
    
    from uuid import uuid4
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

