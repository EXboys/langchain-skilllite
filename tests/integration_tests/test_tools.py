"""Integration tests for SkillLiteTool with real SkillManager.

These tests require the skilllite package to be installed and
a valid skills directory with test skills.
"""

import os
import pytest
import tempfile
from pathlib import Path

# Skip all tests if skilllite is not installed
pytest.importorskip("skilllite")

from skilllite import SkillManager
from langchain_skilllite import SkillLiteTool, SkillLiteToolkit


@pytest.fixture
def temp_skills_dir():
    """Create a temporary skills directory with a test skill."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple calculator skill
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
        main_py.write_text("""import sys
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
    # Parse JSON input from stdin or command line
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
""")

        yield tmpdir


class TestSkillLiteToolIntegration:
    """Integration tests for SkillLiteTool."""

    def test_toolkit_from_directory(self, temp_skills_dir):
        """Test creating toolkit from a skills directory."""
        tools = SkillLiteToolkit.from_directory(
            temp_skills_dir,
            sandbox_level=1,  # No sandbox for testing
        )
        
        assert len(tools) >= 1
        # Find the calculator tool
        calc_tool = next((t for t in tools if t.name == "calculator"), None)
        assert calc_tool is not None
        assert "calculator" in calc_tool.description.lower()

    def test_toolkit_from_manager(self, temp_skills_dir):
        """Test creating toolkit from a SkillManager."""
        manager = SkillManager(skills_dir=temp_skills_dir)
        tools = SkillLiteToolkit.from_manager(
            manager,
            sandbox_level=1,
        )
        
        assert len(tools) >= 1

    def test_tool_has_correct_attributes(self, temp_skills_dir):
        """Test that tools have correct LangChain attributes."""
        tools = SkillLiteToolkit.from_directory(
            temp_skills_dir,
            sandbox_level=1,
        )
        
        for tool in tools:
            # Check required LangChain BaseTool attributes
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "_run")
            assert hasattr(tool, "_arun")
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0

    def test_confirmation_callback_integration(self, temp_skills_dir):
        """Test that confirmation callback is properly integrated."""
        callback_called = False
        
        def test_callback(report: str, scan_id: str) -> bool:
            nonlocal callback_called
            callback_called = True
            return True  # Always confirm
        
        tools = SkillLiteToolkit.from_directory(
            temp_skills_dir,
            sandbox_level=3,
            confirmation_callback=test_callback,
        )
        
        for tool in tools:
            assert tool.confirmation_callback is not None
            assert tool.sandbox_level == 3


class TestSkillLiteToolAsync:
    """Async integration tests for SkillLiteTool."""

    def test_async_method_exists(self, temp_skills_dir):
        """Test that async method exists and is callable."""
        tools = SkillLiteToolkit.from_directory(
            temp_skills_dir,
            sandbox_level=1,
        )

        # Verify async method exists and is callable
        for tool in tools:
            assert hasattr(tool, "_arun")
            assert callable(tool._arun)

