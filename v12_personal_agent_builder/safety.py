"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: SAFETY & HUMAN APPROVAL GUARDRAILS
==============================================================================
Concept & Architecture:
This module implements the Safety Subsystem for Personal Agents (originating in v07).
Autonomous agents with actuators (like file creation or deletion) pose risks if left
unsupervised. The Safety Subsystem introduces a Human-in-the-Loop (HITL) gate:

1. Safety Policies:
   - `Policy.PERMISSIVE`: Allows all tool operations automatically.
   - `Policy.MODERATE`: Requires approval for MODERATE and DANGEROUS actions.
   - `Policy.STRICT`: Requires human confirmation before any tool call is executed.
2. Risk Assessment:
   - Evaluates tool metadata and argument payloads.
   - Flags destructive file operations or sensitive system modifications.
3. Interactive Human Approval Prompt:
   - Displays clear details of the requested tool and parameter values.
   - Allows the user to [Y] Approve, [N] Deny with feedback, or abort.
==============================================================================
"""

import enum
from typing import Dict, Any, Optional, Callable
from tools import Tool


# ==============================================================================
# SECTION 1: SAFETY POLICY LEVELS
# ==============================================================================

class SafetyPolicy(enum.Enum):
    """Enumeration of safety strictness levels."""
    PERMISSIVE = "permissive"   # Auto-approve everything
    MODERATE = "moderate"       # Require approval for MODERATE and DANGEROUS tools
    STRICT = "strict"           # Require approval for all tools regardless of risk


# ==============================================================================
# SECTION 2: SAFETY CONTROLLER
# ==============================================================================

class SafetyController:
    """
    Evaluates risk and orchestrates human-in-the-loop verification before tool execution.
    """

    def __init__(
        self,
        policy: SafetyPolicy = SafetyPolicy.MODERATE,
        approval_callback: Optional[Callable[[str, Dict[str, Any], str], bool]] = None
    ):
        """
        Parameters:
        -----------
        policy : SafetyPolicy
            The enforcement policy level.
        approval_callback : Optional[Callable]
            Optional custom function for UI/GUI approvals. If None, uses terminal stdin.
        """
        self.policy = policy
        self.approval_callback = approval_callback

    def check_approval(self, tool: Tool, arguments: Dict[str, Any]) -> (bool, str):
        """
        Determines whether tool execution requires human approval, and prompts if necessary.

        Parameters:
        -----------
        tool : Tool
            The tool requested by the agent.
        arguments : dict
            The arguments passed to the tool.

        Returns:
        --------
        (bool, str) : Tuple of (is_approved, explanation_message)
        """
        # Rule 1: Permissive policy automatically passes
        if self.policy == SafetyPolicy.PERMISSIVE:
            return True, "Automatically approved under PERMISSIVE policy."

        # Rule 2: Moderate policy checks risk level
        needs_approval = False
        if self.policy == SafetyPolicy.STRICT:
            needs_approval = True
        elif self.policy == SafetyPolicy.MODERATE:
            if tool.risk_level in ("MODERATE", "DANGEROUS"):
                needs_approval = True

        # If operation is deemed safe and doesn't require approval
        if not needs_approval:
            return True, f"Operation '{tool.name}' is SAFE under {self.policy.name} policy."

        # Execute human approval mechanism
        if self.approval_callback:
            approved = self.approval_callback(tool.name, arguments, tool.risk_level)
        else:
            approved = self._terminal_approval_prompt(tool, arguments)

        if approved:
            return True, "User granted approval for execution."
        else:
            return False, f"User REJECTED tool execution for '{tool.name}'."

    def _terminal_approval_prompt(self, tool: Tool, arguments: Dict[str, Any]) -> bool:
        """
        Prompts the human user for interactive confirmation via CLI terminal.

        Returns:
        --------
        bool : True if user accepted, False otherwise.
        """
        print("\n" + "!" * 60)
        print("SAFETY GUARD: HUMAN APPROVAL REQUIRED")
        print("!" * 60)
        print(f"Tool Requested: {tool.name}")
        print(f"Risk Level:     {tool.risk_level}")
        print(f"Description:    {tool.description}")
        print(f"Arguments:      {arguments}")
        print("-" * 60)

        try:
            choice = input("Do you authorize this action? [Y/n]: ").strip().lower()
            return choice in ("y", "yes", "")
        except (KeyboardInterrupt, EOFError):
            print("\nAction cancelled by user.")
            return False
