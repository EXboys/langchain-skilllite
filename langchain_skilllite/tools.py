"""
LangChain tools for SkillLite skill execution.

This module provides LangChain-compatible tool wrappers for SkillLite skills.

IMPORTANT: This is now a lightweight wrapper around the core skilllite SDK.
All types and core logic are imported from skilllite.core.adapters.langchain
and skilllite.core.protocols. This eliminates code duplication and ensures
consistency across all integration points.

For direct SDK usage, import from:
- skilllite.core.adapters.langchain: SkillLiteTool, SkillLiteToolkit
- skilllite.core.protocols: SecurityScanResult, ConfirmationCallback
"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

# Import core classes from skilllite SDK - Single Source of Truth
# This eliminates the ~500 lines of duplicate code that was here before
from skilllite.core.adapters.langchain import (
    SkillLiteTool,
    SkillLiteToolkit,
)
from skilllite.core.protocols import (
    SecurityScanResult,
    ConfirmationCallback,
    AsyncConfirmationCallback,
)

# Re-export for backward compatibility
from skilllite import SkillManager, SkillInfo

if TYPE_CHECKING:
    from pathlib import Path


# ============================================================================
# Extended SkillLiteToolkit with from_directory convenience method
# The core SkillLiteTool and SkillLiteToolkit are imported from skilllite SDK
# ============================================================================

class ExtendedSkillLiteToolkit:
    """
    Extended LangChain Toolkit for SkillLite with additional convenience methods.

    This class extends the core SkillLiteToolkit with:
    - from_directory: Load skills directly from a directory path

    For basic usage, use the imported SkillLiteToolkit directly.
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
        """
        Create LangChain tools from a skills directory.

        Convenience method that creates a SkillManager and loads all skills.

        Args:
            skills_dir: Path to directory containing skill folders
            skill_names: Optional list of skill names to include
            allow_network: Whether to allow network access
            timeout: Execution timeout in seconds
            sandbox_level: Sandbox security level (1/2/3)
            confirmation_callback: Sync callback for security confirmation
            async_confirmation_callback: Async callback for security confirmation

        Returns:
            List of SkillLiteTool instances
        """
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


# Add from_directory method to the imported SkillLiteToolkit for backward compatibility
# This allows users to call SkillLiteToolkit.from_directory() as before
SkillLiteToolkit.from_directory = staticmethod(ExtendedSkillLiteToolkit.from_directory)
