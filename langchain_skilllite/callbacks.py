"""
LangChain callback handlers for SkillLite.

This module provides callback handlers for integrating SkillLite
with LangChain's callback system for logging, tracing, and monitoring.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

if TYPE_CHECKING:
    from langchain_core.agents import AgentAction, AgentFinish
    from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


class SkillLiteCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for SkillLite skill execution.

    This handler logs skill execution events and can be used for
    monitoring, debugging, and auditing SkillLite tool usage.

    Usage:
        from langchain_skilllite import SkillLiteCallbackHandler

        handler = SkillLiteCallbackHandler(verbose=True)

        # Use with LangChain agent
        agent.invoke({"input": "..."}, config={"callbacks": [handler]})

    Attributes:
        verbose: Whether to print execution details
        execution_log: List of execution events
    """

    def __init__(
        self,
        verbose: bool = False,
        log_level: int = logging.INFO,
    ):
        """
        Initialize the callback handler.

        Args:
            verbose: If True, print execution details to stdout
            log_level: Logging level for internal logging
        """
        super().__init__()
        self.verbose = verbose
        self.log_level = log_level
        self.execution_log: List[Dict[str, Any]] = []
        self._current_tool: Optional[str] = None

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "unknown")
        self._current_tool = tool_name

        event = {
            "event": "tool_start",
            "tool_name": tool_name,
            "run_id": str(run_id),
            "input": input_str[:200] if input_str else None,
        }
        self.execution_log.append(event)

        if self.verbose:
            print(f"🔧 [SkillLite] Starting tool: {tool_name}")
            logger.log(self.log_level, f"Tool started: {tool_name}")

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool finishes."""
        # Handle different output types (str, ToolMessage, etc.)
        if isinstance(output, str):
            output_preview = output[:200] if output else None
        elif hasattr(output, "content"):
            # ToolMessage or similar object
            content = output.content
            output_preview = content[:200] if isinstance(content, str) and content else str(content)[:200]
        else:
            output_preview = str(output)[:200] if output else None

        event = {
            "event": "tool_end",
            "tool_name": self._current_tool,
            "run_id": str(run_id),
            "output_preview": output_preview,
            "success": True,
        }
        self.execution_log.append(event)

        if self.verbose:
            print(f"✅ [SkillLite] Tool completed: {self._current_tool}")
            logger.log(self.log_level, f"Tool completed: {self._current_tool}")

        self._current_tool = None

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool errors."""
        event = {
            "event": "tool_error",
            "tool_name": self._current_tool,
            "run_id": str(run_id),
            "error": str(error),
            "success": False,
        }
        self.execution_log.append(event)

        if self.verbose:
            print(f"❌ [SkillLite] Tool error: {self._current_tool} - {error}")
            logger.error(f"Tool error: {self._current_tool} - {error}")

        self._current_tool = None

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of all execution events."""
        total = len(self.execution_log)
        tool_starts = sum(1 for e in self.execution_log if e["event"] == "tool_start")
        tool_ends = sum(1 for e in self.execution_log if e["event"] == "tool_end")
        tool_errors = sum(1 for e in self.execution_log if e["event"] == "tool_error")

        return {
            "total_events": total,
            "tool_executions": tool_starts,
            "successful": tool_ends,
            "errors": tool_errors,
            "success_rate": tool_ends / tool_starts if tool_starts > 0 else 0,
        }

    def clear_log(self) -> None:
        """Clear the execution log."""
        self.execution_log.clear()

