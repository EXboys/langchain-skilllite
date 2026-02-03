# langchain-skilllite

[![PyPI version](https://badge.fury.io/py/langchain-skilllite.svg)](https://badge.fury.io/py/langchain-skilllite)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LangChain integration for [SkillLite](https://github.com/EXboys/skilllite) - a lightweight sandboxed Python skill execution engine.

## Features

- 🔒 **Sandboxed Execution** - All skills run in a Rust-based sandbox (skillbox)
- 📝 **Declarative Skills** - Define skills via SKILL.md, no Python wrappers needed
- 🔍 **Security Scanning** - Pre-execution code analysis for dangerous operations
- ✅ **Confirmation Callbacks** - User approval for high-severity security issues
- ⚡ **Async Support** - Full async support for LangGraph agents

## Installation

```bash
pip install langchain-skilllite
```

This will also install the required dependencies:
- `langchain-core>=0.3.0`
- `skilllite>=0.1.1`

## Quick Start

```python
from langchain_skilllite import SkillLiteToolkit
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Load all skills from a directory as LangChain tools
tools = SkillLiteToolkit.from_directory("./skills")

# Create a LangGraph agent
agent = create_react_agent(ChatOpenAI(model="gpt-4"), tools)

# Run the agent
result = agent.invoke({
    "messages": [("user", "Calculate 15 + 27 using the calculator skill")]
})
```

## Usage

### Basic Usage with SkillManager

```python
from skilllite import SkillManager
from langchain_skilllite import SkillLiteToolkit

# Create a SkillManager
manager = SkillManager(skills_dir="./skills")

# Convert all skills to LangChain tools
tools = SkillLiteToolkit.from_manager(manager)

# Or select specific skills
tools = SkillLiteToolkit.from_manager(
    manager,
    skill_names=["calculator", "web_search"],
    allow_network=True,
    timeout=60
)
```

### Security Levels

SkillLite supports three sandbox security levels:

| Level | Description |
|-------|-------------|
| 1 | No sandbox - direct execution (fastest, least secure) |
| 2 | Sandbox isolation only |
| 3 | Sandbox + security scanning (default, most secure) |

```python
# Level 3 with confirmation callback for high-severity issues
def confirm_execution(report: str, scan_id: str) -> bool:
    print(report)
    return input("Proceed? [y/N]: ").lower() == 'y'

tools = SkillLiteToolkit.from_directory(
    "./skills",
    sandbox_level=3,
    confirmation_callback=confirm_execution
)
```

### Async Confirmation (for LangGraph)

```python
import asyncio

async def async_confirm(report: str, scan_id: str) -> bool:
    print(report)
    # In a real app, this might be a UI prompt
    return True

tools = SkillLiteToolkit.from_directory(
    "./skills",
    sandbox_level=3,
    async_confirmation_callback=async_confirm
)
```

### Callback Handler for Monitoring

```python
from langchain_skilllite import SkillLiteCallbackHandler

handler = SkillLiteCallbackHandler(verbose=True)

# Use with agent
result = agent.invoke(
    {"messages": [("user", "Run my skill")]},
    config={"callbacks": [handler]}
)

# Get execution summary
print(handler.get_execution_summary())
```

## API Reference

### SkillLiteTool

LangChain `BaseTool` adapter for a single SkillLite skill.

### SkillLiteToolkit

Factory class for creating multiple `SkillLiteTool` instances.

- `from_manager(manager, ...)` - Create tools from a SkillManager
- `from_directory(skills_dir, ...)` - Create tools from a skills directory

### SkillLiteCallbackHandler

LangChain callback handler for monitoring skill execution.

## Requirements

- Python >= 3.9
- langchain-core >= 0.3.0
- skilllite >= 0.1.1

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [SkillLite Repository](https://github.com/EXboys/skilllite)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

