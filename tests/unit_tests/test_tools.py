"""Unit tests for SkillLiteTool and SkillLiteToolkit."""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional

from langchain_skilllite.tools import (
    SkillLiteTool,
    SkillLiteToolkit,
    SecurityScanResult,
)


@dataclass
class MockSkillInfo:
    """Mock skill info for testing."""
    name: str
    description: Optional[str] = None


@dataclass
class MockExecutionResult:
    """Mock execution result."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


class TestSecurityScanResult:
    """Tests for SecurityScanResult dataclass."""

    def test_is_safe_no_issues(self):
        """Test that scan with no issues is safe."""
        result = SecurityScanResult(is_safe=True, issues=[])
        assert result.is_safe is True
        assert result.requires_confirmation is False

    def test_requires_confirmation_high_severity(self):
        """Test that high severity issues require confirmation."""
        result = SecurityScanResult(
            is_safe=False,
            issues=[{"severity": "High", "description": "test"}],
            high_severity_count=1,
        )
        assert result.requires_confirmation is True

    def test_format_report_no_issues(self):
        """Test report formatting with no issues."""
        result = SecurityScanResult(is_safe=True, issues=[], scan_id="test-123")
        report = result.format_report()
        assert "No issues found" in report

    def test_format_report_with_issues(self):
        """Test report formatting with issues."""
        result = SecurityScanResult(
            is_safe=False,
            issues=[
                {
                    "severity": "High",
                    "issue_type": "DangerousCode",
                    "description": "Dangerous operation",
                    "rule_id": "SEC001",
                    "line_number": 10,
                    "code_snippet": "os.system('rm -rf /')",
                }
            ],
            scan_id="test-456",
            high_severity_count=1,
        )
        report = result.format_report()
        assert "High" in report
        assert "DangerousCode" in report
        assert "Confirmation required" in report


class TestSkillLiteTool:
    """Tests for SkillLiteTool class."""

    def test_tool_creation(self):
        """Test basic tool creation."""
        mock_manager = MagicMock()
        
        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=mock_manager,
            skill_name="test_skill",
        )
        
        assert tool.name == "test_skill"
        assert tool.description == "A test skill"
        assert tool.sandbox_level == 3  # default

    def test_tool_with_custom_sandbox_level(self):
        """Test tool with custom sandbox level."""
        mock_manager = MagicMock()
        
        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=mock_manager,
            skill_name="test_skill",
            sandbox_level=1,
        )
        
        assert tool.sandbox_level == 1

    def test_run_success(self):
        """Test successful skill execution."""
        mock_manager = MagicMock()
        mock_manager.execute.return_value = MockExecutionResult(
            success=True,
            output="Hello, World!"
        )
        
        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=mock_manager,
            skill_name="test_skill",
            sandbox_level=1,  # No security scan
        )
        
        result = tool._run(param1="value1")
        
        assert result == "Hello, World!"
        mock_manager.execute.assert_called_once()

    def test_run_failure(self):
        """Test failed skill execution."""
        mock_manager = MagicMock()
        mock_manager.execute.return_value = MockExecutionResult(
            success=False,
            error="Skill not found"
        )
        
        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=mock_manager,
            skill_name="test_skill",
            sandbox_level=1,
        )
        
        result = tool._run()
        
        assert "Error" in result
        assert "Skill not found" in result


class TestSkillLiteToolkit:
    """Tests for SkillLiteToolkit class."""

    def test_from_manager_creates_tools(self):
        """Test that from_manager creates tools for each skill."""
        mock_manager = MagicMock()
        mock_manager.list_executable_skills.return_value = [
            MockSkillInfo(name="skill1", description="First skill"),
            MockSkillInfo(name="skill2", description="Second skill"),
        ]
        
        tools = SkillLiteToolkit.from_manager(mock_manager)
        
        assert len(tools) == 2
        assert tools[0].name == "skill1"
        assert tools[1].name == "skill2"

    def test_from_manager_filters_by_name(self):
        """Test that from_manager filters skills by name."""
        mock_manager = MagicMock()
        mock_manager.list_executable_skills.return_value = [
            MockSkillInfo(name="skill1", description="First skill"),
            MockSkillInfo(name="skill2", description="Second skill"),
            MockSkillInfo(name="skill3", description="Third skill"),
        ]
        
        tools = SkillLiteToolkit.from_manager(
            mock_manager,
            skill_names=["skill1", "skill3"]
        )
        
        assert len(tools) == 2
        assert tools[0].name == "skill1"
        assert tools[1].name == "skill3"

    def test_from_manager_passes_options(self):
        """Test that from_manager passes options to tools."""
        mock_manager = MagicMock()
        mock_manager.list_executable_skills.return_value = [
            MockSkillInfo(name="skill1", description="First skill"),
        ]
        
        tools = SkillLiteToolkit.from_manager(
            mock_manager,
            allow_network=True,
            timeout=60,
            sandbox_level=2,
        )
        
        assert len(tools) == 1
        assert tools[0].allow_network is True
        assert tools[0].timeout == 60
        assert tools[0].sandbox_level == 2

