"""
Core types and skill management for langchain-skilllite.

Uses skilllite's scan_code, execute_code, run_skill APIs.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Lazy import skilllite to avoid circular deps
def _get_skilllite():
    try:
        import skilllite
        return skilllite
    except ImportError:
        return None


@dataclass
class SkillInfo:
    """Metadata about a skill loaded from a directory."""

    name: str
    description: str
    skill_dir: str
    entry_point: str = ""

    def get_full_content(self) -> str:
        """Return description (for tool description)."""
        return self.description or f"Skill: {self.name}"


@dataclass
class SecurityScanResult:
    """Result of a security scan (from skilllite.scan_code)."""

    is_safe: bool
    issues: List[Dict[str, Any]]
    requires_confirmation: bool = False
    scan_id: str = ""
    high_severity_count: int = 0

    def format_report(self) -> str:
        """Format scan result as human-readable report."""
        if self.is_safe and not self.issues:
            return "✅ No issues found. Code is safe to execute.\n"
        lines = []
        for i, issue in enumerate(self.issues, 1):
            sev = issue.get("severity", "Unknown")
            desc = issue.get("description", issue.get("message", "Unknown"))
            rule = issue.get("rule_id", "")
            line_num = issue.get("line_number", 0)
            snippet = issue.get("code_snippet", "")
            lines.append(f"  {i}. [{sev}] {desc}")
            if rule:
                lines.append(f"     Rule: {rule}")
            if line_num:
                lines.append(f"     Line: {line_num}")
            if snippet:
                lines.append(f"     Code: {snippet[:80]}...")
        if self.requires_confirmation:
            lines.append("\n⚠️ Confirmation required before execution.")
        return "\n".join(lines)


# Type aliases for callbacks
ConfirmationCallback = Callable[[str, str], bool]
AsyncConfirmationCallback = Callable[[str, str], Any]  # Awaitable[bool]


def _parse_skill_md(skill_dir: Path) -> Optional[Dict[str, Any]]:
    """Parse SKILL.md frontmatter (name, description, entry_point). Returns None if not found."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    content = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    meta = {}
    for line in match.group(1).strip().split("\n"):
        m = re.match(r"^(\w[\w_-]*)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1].replace('\\"', '"')
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1].replace("\\'", "'")
            meta[key] = val
    return meta if meta else None


def _detect_entry_point(skill_dir: Path) -> str:
    """Auto-detect entry point from scripts/ directory."""
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists() or not scripts_dir.is_dir():
        return ""
    candidates = []
    for f in scripts_dir.iterdir():
        if f.is_file() and not f.name.startswith(".") and not f.name.startswith("test_"):
            if f.suffix in (".py", ".js", ".ts", ".sh"):
                if not f.name.endswith("_test.py"):
                    candidates.append(f.name)
    # Prefer main.py, then script.py, then first alphabetically
    for pref in ("main.py", "main.js", "script.py", "script.js"):
        if pref in candidates:
            return f"scripts/{pref}"
    if candidates:
        candidates.sort()
        return f"scripts/{candidates[0]}"
    return ""


def _run_skill_fallback(
    skill_dir: str,
    input_json: str,
    *,
    sandbox_level: int = 3,
    allow_network: bool = False,
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """
    Fallback when skilllite.run_skill is not available (e.g. older PyPI skilllite).
    Calls the skilllite binary directly.
    """
    try:
        from skilllite import get_binary
    except ImportError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "skilllite not installed",
            "exit_code": 1,
            "text": "skilllite not installed",
        }
    binary = get_binary()
    if not binary:
        return {
            "success": False,
            "stdout": "",
            "stderr": "skilllite binary not found",
            "exit_code": 1,
            "text": "skilllite binary not found",
        }
    import subprocess

    cmd = [
        binary,
        "run",
        skill_dir,
        input_json,
        "--sandbox-level",
        str(sandbox_level),
    ]
    if allow_network:
        cmd.append("--allow-network")

    env = dict(os.environ)
    if auto_approve:
        env["SKILLBOX_AUTO_APPROVE"] = "1"

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=os.getcwd(),
        env=env,
    )
    text = (result.stdout or "") + (result.stderr or "")
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout or "",
        "stderr": result.stderr or "",
        "exit_code": result.returncode,
        "text": text.strip(),
    }


class SkillManager:
    """
    Manages skills from a directory. Parses SKILL.md and lists executable skills.
    """

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir).resolve()
        self._skills: Dict[str, SkillInfo] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """Load all skills from the skills directory."""
        if not self.skills_dir.exists() or not self.skills_dir.is_dir():
            return
        for item in self.skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                meta = _parse_skill_md(item)
                if meta:
                    name = meta.get("name", item.name)
                    desc = meta.get("description", "")
                    entry = meta.get("entry_point", "") or _detect_entry_point(item)
                    self._skills[name] = SkillInfo(
                        name=name,
                        description=desc,
                        skill_dir=str(item),
                        entry_point=entry,
                    )

    def list_skills(self) -> List[SkillInfo]:
        """List all loaded skills."""
        return list(self._skills.values())

    def list_executable_skills(self) -> List[SkillInfo]:
        """List skills that have an entry point (can be executed)."""
        return [s for s in self._skills.values() if s.entry_point]

    def get_skill(self, name: str) -> Optional[SkillInfo]:
        """Get skill by name."""
        return self._skills.get(name)

    def execute(
        self,
        skill_name: str,
        input_dict: Dict[str, Any],
        *,
        sandbox_level: int = 3,
        allow_network: bool = False,
        auto_approve: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a skill with the given input.

        Returns dict with output, exit_code, success.
        """
        sl = _get_skilllite()
        if not sl:
            return {
                "success": False,
                "output": "",
                "exit_code": 1,
                "error": "skilllite not installed. Run: pip install skilllite",
            }
        skill = self.get_skill(skill_name)
        if not skill:
            return {
                "success": False,
                "output": "",
                "exit_code": 1,
                "error": f"Skill '{skill_name}' not found",
            }
        if not skill.entry_point:
            return {
                "success": False,
                "output": "",
                "exit_code": 1,
                "error": f"Skill '{skill_name}' has no executable entry point",
            }
        input_json = json.dumps(input_dict)
        run_skill_fn = getattr(sl, "run_skill", None)
        if run_skill_fn is not None:
            result = run_skill_fn(
                skill.skill_dir,
                input_json,
                sandbox_level=sandbox_level,
                allow_network=allow_network,
                auto_approve=auto_approve,
            )
        else:
            result = _run_skill_fallback(
                skill.skill_dir,
                input_json,
                sandbox_level=sandbox_level,
                allow_network=allow_network,
                auto_approve=auto_approve,
            )
        return {
            "success": result.get("success", False),
            "output": result.get("stdout", result.get("text", "")),
            "exit_code": result.get("exit_code", 1),
            "error": result.get("stderr", "") if not result.get("success") else "",
        }
