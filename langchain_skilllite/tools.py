"""
LangChain tools for SkillLite skill execution.

Uses skilllite's scan_code, run_skill APIs. No dependency on skilllite.core.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain_core.tools import BaseTool

from langchain_skilllite.core import (
    ConfirmationCallback,
    AsyncConfirmationCallback,
    SecurityScanResult,
    SkillInfo,
    SkillManager,
)


def _run_skill_with_scan(
    skill: SkillInfo,
    input_json: str,
    sandbox_level: int,
    allow_network: bool,
    confirmation_callback: Optional[ConfirmationCallback],
    async_confirmation_callback: Optional[AsyncConfirmationCallback],
) -> str:
    """Run skill, with optional pre-scan and confirmation for sandbox_level 3."""
    import skilllite

    if not hasattr(skilllite, "run_skill"):
        return "Error: skilllite>=0.1.8 required (run_skill not found). Run: pip install -U skilllite"

    confirmed = False
    if sandbox_level == 3 and confirmation_callback:
        # Pre-scan the entry point script
        entry_path = Path(skill.skill_dir) / skill.entry_point
        if entry_path.exists():
            code = entry_path.read_text(encoding="utf-8")
            lang = "python" if skill.entry_point.endswith(".py") else "javascript" if skill.entry_point.endswith((".js", ".ts")) else "bash"
            scan_result = skilllite.scan_code(lang, code)
            result = SecurityScanResult(
                is_safe=scan_result.get("is_safe", False),
                issues=scan_result.get("issues", []),
                requires_confirmation=scan_result.get("requires_confirmation", False),
                scan_id=scan_result.get("scan_id", ""),
                high_severity_count=sum(1 for i in scan_result.get("issues", []) if i.get("severity") == "High"),
            )
            if result.requires_confirmation:
                report = result.format_report()
                confirmed = confirmation_callback(report, result.scan_id)
                if not confirmed:
                    return f"Error: User did not confirm execution. Security report:\n{report}"

    # Auto-approve when: no sandbox scan (L1/L2), or we confirmed via callback
    auto_approve = sandbox_level < 3 or confirmed
    result = skilllite.run_skill(
        skill.skill_dir,
        input_json,
        sandbox_level=sandbox_level,
        allow_network=allow_network,
        auto_approve=auto_approve,
    )
    if result.get("success"):
        return result.get("stdout", result.get("text", ""))
    return f"Error: {result.get('stderr', result.get('text', 'Execution failed'))}"


class SkillLiteTool(BaseTool):
    """
    LangChain tool that wraps a SkillLite skill.
    """

    name: str
    description: str
    manager: SkillManager
    skill_name: str
    sandbox_level: int = 3
    allow_network: bool = False
    timeout: Optional[int] = None
    confirmation_callback: Optional[ConfirmationCallback] = None
    async_confirmation_callback: Optional[AsyncConfirmationCallback] = None

    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Execute the skill with the given input (as kwargs or JSON string)."""
        if kwargs:
            input_json = json.dumps(kwargs)
        elif args and isinstance(args[0], str):
            try:
                json.loads(args[0])
                input_json = args[0]
            except json.JSONDecodeError:
                input_json = json.dumps({"input": args[0]})
        elif args:
            input_json = json.dumps({"input": str(args[0])})
        else:
            input_json = "{}"

        skill = self.manager.get_skill(self.skill_name)
        if not skill:
            return f"Error: Skill '{self.skill_name}' not found"
        if not skill.entry_point:
            return f"Error: Skill '{self.skill_name}' has no executable entry point"

        return _run_skill_with_scan(
            skill=skill,
            input_json=input_json,
            sandbox_level=self.sandbox_level,
            allow_network=self.allow_network,
            confirmation_callback=self.confirmation_callback,
            async_confirmation_callback=self.async_confirmation_callback,
        )

    async def _arun(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Async execute - runs sync _run in executor."""
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._run(*args, **kwargs),
        )


class SkillLiteToolkit:
    """
    Factory for creating SkillLiteTool instances from a directory or manager.
    """

    @staticmethod
    def from_directory(
        skills_dir: str,
        skill_names: Optional[List[str]] = None,
        allow_network: bool = False,
        timeout: Optional[int] = None,
        sandbox_level: int = 3,
        confirmation_callback: Optional[ConfirmationCallback] = None,
        async_confirmation_callback: Optional[AsyncConfirmationCallback] = None,
    ) -> List[SkillLiteTool]:
        """Create LangChain tools from a skills directory."""
        manager = SkillManager(skills_dir=skills_dir)
        return SkillLiteToolkit.from_manager(
            manager=manager,
            skill_names=skill_names,
            allow_network=allow_network,
            timeout=timeout,
            sandbox_level=sandbox_level,
            confirmation_callback=confirmation_callback,
            async_confirmation_callback=async_confirmation_callback,
        )

    @staticmethod
    def from_manager(
        manager: SkillManager,
        skill_names: Optional[List[str]] = None,
        allow_network: bool = False,
        timeout: Optional[int] = None,
        sandbox_level: int = 3,
        confirmation_callback: Optional[ConfirmationCallback] = None,
        async_confirmation_callback: Optional[AsyncConfirmationCallback] = None,
    ) -> List[SkillLiteTool]:
        """Create LangChain tools from a SkillManager."""
        skills = manager.list_executable_skills()
        if skill_names:
            skills = [s for s in skills if s.name in skill_names]
        tools = []
        for skill in skills:
            tools.append(
                SkillLiteTool(
                    name=skill.name,
                    description=skill.get_full_content(),
                    manager=manager,
                    skill_name=skill.name,
                    sandbox_level=sandbox_level,
                    allow_network=allow_network,
                    timeout=timeout,
                    confirmation_callback=confirmation_callback,
                    async_confirmation_callback=async_confirmation_callback,
                )
            )
        return tools
