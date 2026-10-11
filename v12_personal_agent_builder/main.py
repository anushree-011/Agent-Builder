"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: INTERACTIVE STUDIO CLI
==============================================================================
Concept & Architecture:
This is the master interactive Command Line Interface for Version 12.
It serves as the "Personal Agent Builder Studio", allowing users to build and run
custom AI agents tailored to their exact specifications.

User Interaction Modes:
1. Natural Language Builder:
   - "You type what kind of agent you want, and it builds it!"
   - Example: "Build a coding agent with file access and human approval."
2. Pre-configured Presets:
   - Instant access to CodeCraft, ScholarAgent, PythagorasAgent, or SentinelFileAgent.
3. Custom Interactive Wizard:
   - Step-by-step interactive configuration of Persona, Goal, Tools, Memory, Safety,
     Planning, and Self-Reflection.

Execution:
python main.py
==============================================================================
"""

import os
import sys
from dotenv import load_dotenv

from builder import AgentBuilder, NaturalLanguageAgentBuilder
from presets import (
    build_coding_agent,
    build_research_agent,
    build_math_tutor_agent,
    build_sentinel_file_agent
)
from safety import SafetyPolicy
from agent import PersonalAgent


# ==============================================================================
# SECTION 1: ENVIRONMENT CONFIGURATION
# ==============================================================================

# Load environment variables from parent or current .env
load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)
MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemma4:31b"
)


def validate_environment():
    """Ensures necessary API credentials are present."""
    if not OLLAMA_API_KEY:
        print("\n" + "=" * 60)
        print("ERROR: OLLAMA_API_KEY is not defined in your environment or .env file.")
        print("Please configure your .env file with a valid API key.")
        print("=" * 60 + "\n")
        sys.exit(1)


# ==============================================================================
# SECTION 2: INTERACTIVE REPL WITH CREATED AGENT
# ==============================================================================

def run_agent_repl(agent: PersonalAgent):
    """
    Launches an interactive chat session with the customized agent.

    Parameters:
    -----------
    agent : PersonalAgent
        The configured agent instance to interact with.
    """
    print("\n" + "=" * 60)
    print(f"AGENT ACTIVATED: {agent.name.upper()}")
    print("=" * 60)
    print(f"Goal:       {agent.goal}")
    print(f"Tools:      {[t.name for t in agent.tools.list_tools()]}")
    print(f"Safety:     {agent.safety.policy.name}")
    print(f"Planning:   {'Enabled' if agent.enable_planning else 'Disabled'}")
    print(f"Reflection: {'Enabled' if agent.enable_reflection else 'Disabled'}")
    print("=" * 60)
    print("Type 'exit' to return to Builder Studio.\n")

    while True:
        try:
            user_input = input(f"\nYou -> [{agent.name}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nReturning to main menu...")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "menu"):
            print(f"Deactivating {agent.name}.")
            break

        try:
            # Execute agent reasoning loop
            response = agent.run(user_input)

            print(f"\n[{agent.name} Response]:")
            print("-" * 60)
            print(response)
            print("-" * 60)

        except Exception as error:
            print(f"\n[Execution Error]: {error}")


# ==============================================================================
# SECTION 3: BUILDER STUDIO MENU OPTIONS
# ==============================================================================

def mode_natural_language_builder():
    """Option 1: Build an agent using natural language specifications."""
    print("\n" + "=" * 60)
    print("NATURAL LANGUAGE AGENT BUILDER")
    print("=" * 60)
    print("Describe the agent you wish to create in plain English.")
    print("Examples:")
    print("  - 'Build a coding agent with file access and human approval.'")
    print("  - 'Create a research agent that remembers notes and evaluates its answers.'")
    print("  - 'Make a math tutor agent that uses a calculator.'")
    print("-" * 60)

    prompt = input("\nEnter your agent description: ").strip()
    if not prompt:
        print("No description provided. Returning to main menu.")
        return

    meta_builder = NaturalLanguageAgentBuilder(
        api_key=OLLAMA_API_KEY,
        base_url=OLLAMA_BASE_URL,
        model_name=MODEL_NAME
    )

    agent = meta_builder.build_from_prompt(prompt)
    run_agent_repl(agent)


def mode_presets_menu():
    """Option 2: Launch one of the pre-configured blueprints."""
    print("\n" + "=" * 60)
    print("SELECT AN AGENT PRESET BLUEPRINT")
    print("=" * 60)
    print("1. CodeCraft Agent         -> File operations, Planning, Reflection, Moderate Safety")
    print("2. Scholar Agent           -> Memory store, File summaries, Reflection")
    print("3. Pythagoras Math Agent   -> Safe AST Calculator, Step-by-step Planning")
    print("4. Sentinel File Agent     -> Strict human approval for every file action")
    print("0. Back to Main Menu")
    print("-" * 60)

    choice = input("Enter your selection [1-4]: ").strip()

    if choice == "1":
        agent = build_coding_agent(OLLAMA_API_KEY, OLLAMA_BASE_URL, MODEL_NAME)
    elif choice == "2":
        agent = build_research_agent(OLLAMA_API_KEY, OLLAMA_BASE_URL, MODEL_NAME)
    elif choice == "3":
        agent = build_math_tutor_agent(OLLAMA_API_KEY, OLLAMA_BASE_URL, MODEL_NAME)
    elif choice == "4":
        agent = build_sentinel_file_agent(OLLAMA_API_KEY, OLLAMA_BASE_URL, MODEL_NAME)
    else:
        print("Returning to main menu.")
        return

    run_agent_repl(agent)


def mode_custom_wizard():
    """Option 3: Step-by-step interactive wizard configuring every subsystem."""
    print("\n" + "=" * 60)
    print("CUSTOM AGENT CONFIGURATION WIZARD")
    print("=" * 60)

    name = input("Agent Name (e.g., 'AnalystBot'): ").strip() or "CustomAgent"
    goal = input("Agent Goal: ").strip() or "Assist with specialized tasks"
    persona = input("Agent Persona / System Instructions (optional): ").strip()

    # Tools selection
    print("\nEnable Tools:")
    attach_files = input("  Enable File System Tools? [y/N]: ").strip().lower() == "y"
    attach_math = input("  Enable Safe Calculator Tool? [y/N]: ").strip().lower() == "y"

    # Memory selection
    attach_memory = input("\nEnable Long-Term Persistent Memory? [y/N]: ").strip().lower() == "y"

    # Safety selection
    print("\nSelect Safety Guardrail Policy:")
    print("  1. PERMISSIVE (Auto-approve everything)")
    print("  2. MODERATE   (Confirm state-changing / destructive actions) [Default]")
    print("  3. STRICT     (Confirm all actions)")
    safety_choice = input("Choice [1-3]: ").strip()
    if safety_choice == "1":
        safety_policy = SafetyPolicy.PERMISSIVE
    elif safety_choice == "3":
        safety_policy = SafetyPolicy.STRICT
    else:
        safety_policy = SafetyPolicy.MODERATE

    # Cognitive features
    enable_planning = input("\nEnable Multi-Step Planning Phase? [y/N]: ").strip().lower() == "y"
    enable_reflection = input("Enable Reflection & Self-Evaluation Pass? [y/N]: ").strip().lower() == "y"

    # Assemble using Fluent Builder
    builder = (
        AgentBuilder()
        .with_name(name)
        .with_goal(goal)
        .with_credentials(OLLAMA_API_KEY, OLLAMA_BASE_URL, MODEL_NAME)
        .with_safety(safety_policy)
        .with_planning(enable_planning)
        .with_reflection(enable_reflection)
    )

    if persona:
        builder.with_persona(persona)
    if attach_files:
        builder.with_file_tools()
    if attach_math:
        builder.with_calculator()
    if attach_memory:
        builder.with_memory(storage_path=f"{name.lower()}_memory.json")

    agent = builder.build()
    print(f"\nAgent '{agent.name}' assembled successfully!")
    run_agent_repl(agent)


# ==============================================================================
# SECTION 4: MASTER STUDIO MENU LOOP
# ==============================================================================

def main():
    """Master entry point for the V12 Personal Agent Builder Studio."""
    validate_environment()

    while True:
        print("\n" + "=" * 60)
        print("PERSONAL AGENT BUILDER STUDIO (VERSION 12)")
        print("=" * 60)
        print("1. Natural Language Agent Builder ('Type what you want, it builds it')")
        print("2. Preset Agent Blueprints (Coding, Research, Math, Sentinel)")
        print("3. Custom Agent Step-by-Step Wizard")
        print("0. Exit Studio")
        print("=" * 60)

        try:
            choice = input("\nEnter choice [1, 2, 3, or 0]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Personal Agent Builder Studio. Goodbye!")
            break

        if choice == "1":
            mode_natural_language_builder()
        elif choice == "2":
            mode_presets_menu()
        elif choice == "3":
            mode_custom_wizard()
        elif choice in ("0", "exit", "quit"):
            print("Exiting Personal Agent Builder Studio. Goodbye!")
            break
        else:
            print("Invalid selection. Please choose 1, 2, 3, or 0.")


if __name__ == "__main__":
    main()
