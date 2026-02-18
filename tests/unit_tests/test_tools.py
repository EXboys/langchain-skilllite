"""Unit tests for SkillLiteTool and SkillLiteToolkit."""

import pytest
from unittest.mock import patch
from dataclasses import dataclass
from typing import Optional

from langchain_skilllite.tools import SkillLiteTool, SkillLiteToolkit
from langchain_skilllite.core import SecurityScanResult, SkillManager, SkillInfo


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
            requires_confirmation=True,
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
            requires_confirmation=True,
            scan_id="test-456",
            high_severity_count=1,
        )
        report = result.format_report()
        assert "High" in report
        assert "Dangerous operation" in report
        assert "Confirmation required" in report


class TestSkillLiteTool:
    """Tests for SkillLiteTool class."""

    def test_tool_creation(self, tmp_path):
        """Test basic tool creation."""
        (tmp_path / "test_skill").mkdir()
        (tmp_path / "test_skill" / "SKILL.md").write_text("---\nname: test_skill\ndescription: A test skill\n---")
        (tmp_path / "test_skill" / "scripts").mkdir()
        (tmp_path / "test_skill" / "scripts" / "main.py").write_text("print('ok')")
        manager = SkillManager(skills_dir=str(tmp_path))

        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=manager,
            skill_name="test_skill",
        )

        assert tool.name == "test_skill"
        assert tool.description == "A test skill"
        assert tool.sandbox_level == 3  # default

    def test_tool_with_custom_sandbox_level(self, tmp_path):
        """Test tool with custom sandbox level."""
        (tmp_path / "test_skill").mkdir()
        (tmp_path / "test_skill" / "SKILL.md").write_text("---\nname: test_skill\ndescription: A test skill\n---")
        (tmp_path / "test_skill" / "scripts").mkdir()
        (tmp_path / "test_skill" / "scripts" / "main.py").write_text("print('ok')")
        manager = SkillManager(skills_dir=str(tmp_path))

        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=manager,
            skill_name="test_skill",
            sandbox_level=1,
        )

        assert tool.sandbox_level == 1

    @pytest.mark.skipif(__import__("importlib").util.find_spec("skilllite") is None, reason="skilllite not installed")
    @patch("skilllite.run_skill")
    def test_run_success(self, mock_run_skill, tmp_path):
        """Test successful skill execution via run_skill."""
        mock_run_skill.return_value = {
            "success": True,
            "stdout": "Hello, World!",
            "stderr": "",
            "exit_code": 0,
        }

        (tmp_path / "test_skill").mkdir()
        (tmp_path / "test_skill" / "SKILL.md").write_text("---\nname: test_skill\ndescription: A test skill\n---")
        (tmp_path / "test_skill" / "scripts").mkdir()
        (tmp_path / "test_skill" / "scripts" / "main.py").write_text("print('ok')")
        manager = SkillManager(skills_dir=str(tmp_path))

        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=manager,
            skill_name="test_skill",
            sandbox_level=1,
        )

        result = tool._run(param1="value1")

        assert result == "Hello, World!"
        mock_run_skill.assert_called_once()

    @pytest.mark.skipif(__import__("importlib").util.find_spec("skilllite") is None, reason="skilllite not installed")
    @patch("skilllite.run_skill")
    def test_run_failure(self, mock_run_skill, tmp_path):
        """Test failed skill execution."""
        mock_run_skill.return_value = {
            "success": False,
            "stderr": "Skill not found",
            "exit_code": 1,
        }

        (tmp_path / "test_skill").mkdir()
        (tmp_path / "test_skill" / "SKILL.md").write_text("---\nname: test_skill\ndescription: A test skill\n---")
        (tmp_path / "test_skill" / "scripts").mkdir()
        (tmp_path / "test_skill" / "scripts" / "main.py").write_text("print('ok')")
        manager = SkillManager(skills_dir=str(tmp_path))

        tool = SkillLiteTool(
            name="test_skill",
            description="A test skill",
            manager=manager,
            skill_name="test_skill",
            sandbox_level=1,
        )

        result = tool._run()

        assert "Error" in result
        assert "Skill not found" in result


class TestSkillLiteToolkit:
    """Tests for SkillLiteToolkit class."""

    def test_from_manager_creates_tools(self, tmp_path):
        """Test that from_manager creates tools for each skill."""
        for name in ("skill1", "skill2"):
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name} skill\n---")
            (d / "scripts").mkdir()
            (d / "scripts" / "main.py").write_text("print('ok')")
        manager = SkillManager(skills_dir=str(tmp_path))

        tools = SkillLiteToolkit.from_manager(manager)
        tools_sorted = sorted(tools, key=lambda t: t.name)

        assert len(tools) == 2
        assert tools_sorted[0].name == "skill1"
        assert tools_sorted[1].name == "skill2"

    def test_from_manager_filters_by_name(self, tmp_path):
        """Test that from_manager filters skills by name."""
        for name in ("skill1", "skill2", "skill3"):
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name} skill\n---")
            (d / "scripts").mkdir()
            (d / "scripts" / "main.py").write_text("print('ok')")
        manager = SkillManager(skills_dir=str(tmp_path))

        tools = SkillLiteToolkit.from_manager(
            manager,
            skill_names=["skill1", "skill3"],
        )
        tools_sorted = sorted(tools, key=lambda t: t.name)

        assert len(tools) == 2
        assert tools_sorted[0].name == "skill1"
        assert tools_sorted[1].name == "skill3"

    def test_from_manager_passes_options(self, tmp_path):
        """Test that from_manager passes options to tools."""
        d = tmp_path / "skill1"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: skill1\ndescription: First skill\n---")
        (d / "scripts").mkdir()
        (d / "scripts" / "main.py").write_text("print('ok')")
        manager = SkillManager(skills_dir=str(tmp_path))

        tools = SkillLiteToolkit.from_manager(
            manager,
            allow_network=True,
            timeout=60,
            sandbox_level=2,
        )

        assert len(tools) == 1
        assert tools[0].allow_network is True
        assert tools[0].timeout == 60
        assert tools[0].sandbox_level == 2

