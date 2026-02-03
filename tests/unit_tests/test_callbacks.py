"""Unit tests for SkillLiteCallbackHandler."""

import pytest
from uuid import uuid4

from langchain_skilllite.callbacks import SkillLiteCallbackHandler


class TestSkillLiteCallbackHandler:
    """Tests for SkillLiteCallbackHandler class."""

    def test_handler_creation(self):
        """Test basic handler creation."""
        handler = SkillLiteCallbackHandler()
        
        assert handler.verbose is False
        assert handler.execution_log == []

    def test_handler_verbose_mode(self):
        """Test handler with verbose mode."""
        handler = SkillLiteCallbackHandler(verbose=True)
        
        assert handler.verbose is True

    def test_on_tool_start(self):
        """Test on_tool_start callback."""
        handler = SkillLiteCallbackHandler()
        run_id = uuid4()
        
        handler.on_tool_start(
            serialized={"name": "test_tool"},
            input_str="test input",
            run_id=run_id,
        )
        
        assert len(handler.execution_log) == 1
        assert handler.execution_log[0]["event"] == "tool_start"
        assert handler.execution_log[0]["tool_name"] == "test_tool"
        assert handler._current_tool == "test_tool"

    def test_on_tool_end(self):
        """Test on_tool_end callback."""
        handler = SkillLiteCallbackHandler()
        run_id = uuid4()
        
        # First start the tool
        handler.on_tool_start(
            serialized={"name": "test_tool"},
            input_str="test input",
            run_id=run_id,
        )
        
        # Then end it
        handler.on_tool_end(
            output="test output",
            run_id=run_id,
        )
        
        assert len(handler.execution_log) == 2
        assert handler.execution_log[1]["event"] == "tool_end"
        assert handler.execution_log[1]["success"] is True
        assert handler._current_tool is None

    def test_on_tool_error(self):
        """Test on_tool_error callback."""
        handler = SkillLiteCallbackHandler()
        run_id = uuid4()
        
        # First start the tool
        handler.on_tool_start(
            serialized={"name": "test_tool"},
            input_str="test input",
            run_id=run_id,
        )
        
        # Then error
        handler.on_tool_error(
            error=ValueError("Something went wrong"),
            run_id=run_id,
        )
        
        assert len(handler.execution_log) == 2
        assert handler.execution_log[1]["event"] == "tool_error"
        assert handler.execution_log[1]["success"] is False
        assert "Something went wrong" in handler.execution_log[1]["error"]

    def test_get_execution_summary(self):
        """Test execution summary generation."""
        handler = SkillLiteCallbackHandler()
        run_id1 = uuid4()
        run_id2 = uuid4()
        
        # Simulate two tool executions, one success, one error
        handler.on_tool_start({"name": "tool1"}, "input1", run_id=run_id1)
        handler.on_tool_end("output1", run_id=run_id1)
        
        handler.on_tool_start({"name": "tool2"}, "input2", run_id=run_id2)
        handler.on_tool_error(ValueError("error"), run_id=run_id2)
        
        summary = handler.get_execution_summary()
        
        assert summary["total_events"] == 4
        assert summary["tool_executions"] == 2
        assert summary["successful"] == 1
        assert summary["errors"] == 1
        assert summary["success_rate"] == 0.5

    def test_clear_log(self):
        """Test clearing the execution log."""
        handler = SkillLiteCallbackHandler()
        run_id = uuid4()
        
        handler.on_tool_start({"name": "tool1"}, "input1", run_id=run_id)
        assert len(handler.execution_log) == 1
        
        handler.clear_log()
        assert len(handler.execution_log) == 0

    def test_verbose_output(self, capsys):
        """Test verbose output is printed."""
        handler = SkillLiteCallbackHandler(verbose=True)
        run_id = uuid4()
        
        handler.on_tool_start({"name": "test_tool"}, "input", run_id=run_id)
        
        captured = capsys.readouterr()
        assert "SkillLite" in captured.out
        assert "test_tool" in captured.out

