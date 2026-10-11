"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: PRESET AGENT BLUEPRINTS
==============================================================================
Concept & Purpose:
This module contains turnkey, production-ready agent presets demonstrating
how different combinations of Goal, Persona, Tools, Memory, Safety, Planning,
and Reflection produce specialized autonomous agents.

Available Presets:
1. `Coding Agent`:
   - Capabilities: File system inspection, code writing, multi-step planning.
   - Safety: MODERATE (requires human confirmation before writing/deleting files).
   - Reflection: Enabled (grades its own code for syntax, logic, and clarity).

2. `Research Agent`:
   - Capabilities: Persistent memory store, notes search, file summary generation.
   - Safety: PERMISSIVE.
   - Reflection: Enabled (grades summaries for thoroughness and factual clarity).

3. `Math Tutor Agent`:
   - Capabilities: Safe AST calculator, step-by-step explanation.
   - Safety: PERMISSIVE.
   - Planning: Enabled.
   - Reflection: Enabled (verifies arithmetic accuracy).

4. `Sentinel File Agent`:
   - Capabilities: File and directory manipulation.
   - Safety: STRICT (requires human confirmation before ANY action).
==============================================================================
"""

from builder import AgentBuilder
from safety import SafetyPolicy
from agent import PersonalAgent


def build_coding_agent(
    api_key: str,
    base_url: str = "https://ollama.com/api",
    model_name: str = "gemma4:31b"
) -> PersonalAgent:
    """Creates a specialized Coding Agent with file access, planning, and moderate safety."""
    return (
        AgentBuilder()
        .with_name("CodeCraft")
        .with_goal("Write, refactor, and verify code files safely across the project.")
        .with_persona(
            "You are CodeCraft, a senior software engineering assistant. "
            "You write modular, clean, well-commented code. Always plan before modifying files."
        )
        .with_file_tools()
        .with_safety(SafetyPolicy.MODERATE)
        .with_planning(True)
        .with_reflection(True)
        .with_credentials(api_key, base_url, model_name)
        .build()
    )


def build_research_agent(
    api_key: str,
    base_url: str = "https://ollama.com/api",
    model_name: str = "gemma4:31b",
    storage_path: str = "research_memory.json"
) -> PersonalAgent:
    """Creates a Research Agent with persistent memory and reflection."""
    return (
        AgentBuilder()
        .with_name("ScholarAgent")
        .with_goal("Investigate topics, record key findings, and synthesize structured reports.")
        .with_persona(
            "You are ScholarAgent, an expert research analyst. "
            "You meticulously save discovered facts to memory and cite references accurately."
        )
        .with_memory(storage_path=storage_path)
        .with_file_tools()
        .with_safety(SafetyPolicy.PERMISSIVE)
        .with_planning(True)
        .with_reflection(True)
        .with_credentials(api_key, base_url, model_name)
        .build()
    )


def build_math_tutor_agent(
    api_key: str,
    base_url: str = "https://ollama.com/api",
    model_name: str = "gemma4:31b"
) -> PersonalAgent:
    """Creates a Math Tutor Agent with safe arithmetic and self-evaluation."""
    return (
        AgentBuilder()
        .with_name("PythagorasAgent")
        .with_goal("Solve quantitative problems accurately and teach mathematical concepts clearly.")
        .with_persona(
            "You are PythagorasAgent, an enthusiastic math educator. "
            "Always verify your calculations with the calculate tool and explain step-by-step."
        )
        .with_calculator()
        .with_safety(SafetyPolicy.PERMISSIVE)
        .with_planning(True)
        .with_reflection(True)
        .with_credentials(api_key, base_url, model_name)
        .build()
    )


def build_sentinel_file_agent(
    api_key: str,
    base_url: str = "https://ollama.com/api",
    model_name: str = "gemma4:31b"
) -> PersonalAgent:
    """Creates a high-security File Manager Agent enforcing strict human approval."""
    return (
        AgentBuilder()
        .with_name("SentinelFileAgent")
        .with_goal("Inspect and manage local directories under strict human supervision.")
        .with_persona(
            "You are SentinelFileAgent, a cautious system utility agent. "
            "You explain all file modifications clearly and strictly require authorization."
        )
        .with_file_tools()
        .with_safety(SafetyPolicy.STRICT)
        .with_planning(False)
        .with_reflection(False)
        .with_credentials(api_key, base_url, model_name)
        .build()
    )
