"""
LangChain integration for SkillLite.

This package provides LangChain-compatible tools for executing SkillLite skills
in a sandboxed environment. It acts as a thin adapter layer on top of the
skilllite core package.

Key Features:
- SkillLiteTool: LangChain BaseTool adapter for individual skills
- SkillLiteToolkit: Convenient toolkit for loading multiple skills
- Security scanning and confirmation callbacks for sandbox level 3
- Full async support for LangGraph agents

Installation:
    pip install langchain-skilllite

Quick Start:
    ```python
    from langchain_skilllite import SkillLiteToolkit
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent

    # Load skills as LangChain tools
    tools = SkillLiteToolkit.from_directory("./skills")

    # Use with any LangChain agent
    agent = create_react_agent(ChatOpenAI(), tools)
    result = agent.invoke({"messages": [("user", "Run my skill")]})
    ```

For more information, see:
- SkillLite: https://github.com/EXboys/skilllite
- LangChain: https://python.langchain.com/
"""

from langchain_skilllite.tools import (
    SkillLiteTool,
    SkillLiteToolkit,
)
from langchain_skilllite.callbacks import (
    SkillLiteCallbackHandler,
)
from langchain_skilllite._version import __version__

__all__ = [
    # Core Tools
    "SkillLiteTool",
    "SkillLiteToolkit",
    # Callbacks
    "SkillLiteCallbackHandler",
    # Version
    "__version__",
]

