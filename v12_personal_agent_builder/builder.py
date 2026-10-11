"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: FLUENT & NATURAL LANGUAGE BUILDER
==============================================================================
Concept & Architecture:
This module provides two builder interfaces for creating customized AI agents:

1. `AgentBuilder` (Fluent Programmatic API):
   A clean Builder pattern interface allowing developers to chain configuration options:
   `AgentBuilder().with_name("Coder").with_goal("Refactor files").with_safety(SafetyPolicy.MODERATE).build()`

2. `NaturalLanguageAgentBuilder` (AI Meta-Builder):
   Takes a natural language prompt from a human user:
   "Build a coding agent with file access and human approval."
   Parses the request into structured configuration, binds appropriate tools and
   guardrails, and instantiates the customized agent on the fly!
==============================================================================
"""

import json
from typing import List, Optional

from tools import ToolRegistry, Tool, get_file_tools, get_calculator_tools
from memory import PersistentMemoryStore
from safety import SafetyController, SafetyPolicy
from agent import PersonalAgent


# ==============================================================================
# SECTION 1: FLUENT PROGRAMMATIC BUILDER
# ==============================================================================

class AgentBuilder:
    """
    Fluent builder class for programmatically configuring and instantiating PersonalAgent instances.
    """

    def __init__(self):
        """Initializes default builder parameters."""
        self._name: str = "Assistant"
        self._goal: str = "Assist user with general inquiries"
        self._system_persona: Optional[str] = None
        self._tool_registry: ToolRegistry = ToolRegistry()
        self._memory_store: Optional[PersistentMemoryStore] = None
        self._safety_policy: SafetyPolicy = SafetyPolicy.MODERATE
        self._enable_planning: bool = False
        self._enable_reflection: bool = False
        self._api_key: Optional[str] = None
        self._base_url: str = "https://ollama.com/api"
        self._model_name: str = "gemma4:31b"

    def with_name(self, name: str) -> "AgentBuilder":
        """Sets the agent persona name."""
        self._name = name
        return self

    def with_goal(self, goal: str) -> "AgentBuilder":
        """Sets the primary objective for the agent."""
        self._goal = goal
        return self

    def with_persona(self, persona: str) -> "AgentBuilder":
        """Sets custom instructions defining style and behavioral boundaries."""
        self._system_persona = persona
        return self

    def with_tools(self, tools: List[Tool]) -> "AgentBuilder":
        """Registers a list of tools into the agent's tool registry."""
        for tool in tools:
            self._tool_registry.register(tool)
        return self

    def with_file_tools(self) -> "AgentBuilder":
        """Adds standard file creation, reading, and listing tools."""
        return self.with_tools(get_file_tools())

    def with_calculator(self) -> "AgentBuilder":
        """Adds safe mathematical calculation tool."""
        return self.with_tools(get_calculator_tools())

    def with_memory(self, storage_path: str = "agent_memory.json") -> "AgentBuilder":
        """Enables long-term persistent memory and registers memory tools."""
        self._memory_store = PersistentMemoryStore(storage_path=storage_path)
        self.with_tools(self._memory_store.get_as_tools())
        return self

    def with_safety(self, policy: SafetyPolicy) -> "AgentBuilder":
        """Configures safety guardrail strictness level."""
        self._safety_policy = policy
        return self

    def with_planning(self, enabled: bool = True) -> "AgentBuilder":
        """Enables multi-step planning before execution."""
        self._enable_planning = enabled
        return self

    def with_reflection(self, enabled: bool = True) -> "AgentBuilder":
        """Enables self-evaluation and iterative output refinement."""
        self._enable_reflection = enabled
        return self

    def with_credentials(
        self,
        api_key: str,
        base_url: str = "https://ollama.com/api",
        model_name: str = "gemma4:31b"
    ) -> "AgentBuilder":
        """Configures Ollama Cloud credentials."""
        self._api_key = api_key
        self._base_url = base_url
        self._model_name = model_name
        return self

    def build(self) -> PersonalAgent:
        """
        Constructs and returns the configured PersonalAgent instance.

        Returns:
        --------
        PersonalAgent : Ready-to-run agent instance.
        """
        safety_ctrl = SafetyController(policy=self._safety_policy)

        return PersonalAgent(
            name=self._name,
            goal=self._goal,
            system_persona=self._system_persona,
            tool_registry=self._tool_registry,
            memory_store=self._memory_store,
            safety_controller=safety_ctrl,
            enable_planning=self._enable_planning,
            enable_reflection=self._enable_reflection,
            api_key=self._api_key,
            base_url=self._base_url,
            model_name=self._model_name
        )


# ==============================================================================
# SECTION 2: NATURAL LANGUAGE META-BUILDER
# ==============================================================================

class NaturalLanguageAgentBuilder:
    """
    Parses conversational user descriptions to dynamically construct configured agents.
    Example: "Build a coding agent with file access and human approval."
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ollama.com/api",
        model_name: str = "gemma4:31b"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    def build_from_prompt(self, spec_prompt: str) -> PersonalAgent:
        """
        Parses a natural language agent specification and builds a configured PersonalAgent.

        Parameters:
        -----------
        spec_prompt : str
            User description of the desired agent.

        Returns:
        --------
        PersonalAgent : Instantiated agent matching the user's specification.
        """
        print(f"\n[Meta-Builder] Analyzing specifications for: '{spec_prompt}'")

        # Parse requirements using keyword analysis and intelligent fallbacks
        lower_prompt = spec_prompt.lower()

        # Infer agent name and goal
        if "coding" in lower_prompt or "code" in lower_prompt or "developer" in lower_prompt:
            name = "CodeAgent"
            goal = "Write, inspect, and modify code files safely."
        elif "research" in lower_prompt or "study" in lower_prompt:
            name = "ResearchAgent"
            goal = "Gather facts, organize research notes, and summarize knowledge."
        elif "math" in lower_prompt or "calc" in lower_prompt or "tutor" in lower_prompt:
            name = "MathTutorAgent"
            goal = "Solve math problems and explain calculations step-by-step."
        else:
            name = "CustomPersonalAgent"
            goal = spec_prompt

        builder = (
            AgentBuilder()
            .with_name(name)
            .with_goal(goal)
            .with_credentials(self.api_key, self.base_url, self.model_name)
        )

        # Infer Tools
        if any(w in lower_prompt for w in ["file", "disk", "folder", "code", "directory"]):
            print("  -> Attaching File System Tools")
            builder.with_file_tools()

        if any(w in lower_prompt for w in ["math", "calculator", "calculate", "numbers"]):
            print("  -> Attaching Safe Calculator Tool")
            builder.with_calculator()

        # Infer Memory
        if any(w in lower_prompt for w in ["memory", "remember", "recall", "store", "notes"]):
            print("  -> Attaching Persistent Memory Subsystem")
            builder.with_memory()

        # Infer Safety Policy
        if any(w in lower_prompt for w in ["human approval", "safety", "approval", "strict", "guardrail"]):
            print("  -> Configuring STRICT / MODERATE Human-in-the-Loop Safety")
            builder.with_safety(SafetyPolicy.MODERATE)
        elif "permissive" in lower_prompt or "auto" in lower_prompt or "unsupervised" in lower_prompt:
            print("  -> Configuring PERMISSIVE Safety Policy")
            builder.with_safety(SafetyPolicy.PERMISSIVE)
        else:
            builder.with_safety(SafetyPolicy.MODERATE)

        # Infer Planning
        if any(w in lower_prompt for w in ["plan", "planning", "strategy", "step-by-step", "multi-step"]):
            print("  -> Enabling Multi-Step Planning")
            builder.with_planning(True)

        # Infer Reflection
        if any(w in lower_prompt for w in ["reflect", "reflection", "evaluate", "quality", "review"]):
            print("  -> Enabling Self-Evaluation Reflection Loop")
            builder.with_reflection(True)

        agent = builder.build()
        print(f"[Meta-Builder] Agent '{agent.name}' successfully configured and instantiated!\n")
        return agent
