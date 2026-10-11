"""
==============================================================================
V11 - MULTI-AGENT SYSTEM: MAIN ENTRY POINT
==============================================================================
Concept & Purpose:
This script provides the interactive Command Line Interface (CLI) for Version 11.
It initializes environment variables, configures the Coordinator and Specialist Agents
with Ollama credentials, and runs an interactive REPL loop where users can submit
complex, multi-step requests.

Unlike Version 10 (which routes a task to a single agent), Version 11 demonstrates:
- Automatic task breakdown into sequential subtasks.
- Delegation across multiple specialist agents (File, Memory, Calculator).
- Shared state blackboard tracking progress in real-time.
- Final unified synthesis of all agent results.

Execution:
python main.py
==============================================================================
"""

# Import os for reading environment variables
import os

# Import dotenv to load variables from local .env file
from dotenv import load_dotenv

# Import configuration and pipeline runner for the coordinator agent
from coordinator_agent import (
    configure_coordinator,
    run_coordinator
)

# Import configuration function for specialist agents
from agents import configure_ollama


# ==============================================================================
# SECTION 1: LOAD ENVIRONMENT CONFIGURATION
# ==============================================================================

# Parse and load values from .env
load_dotenv()

# Read Ollama API key
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Read Ollama base URL, defaulting to cloud endpoint
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)

# Read model identifier, defaulting to gemma4:31b
MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemma4:31b"
)


# ==============================================================================
# SECTION 2: ENVIRONMENT VALIDATION
# ==============================================================================

# Guard check: Ensure API key is present
if not OLLAMA_API_KEY:
    print("ERROR: OLLAMA_API_KEY is missing from environment or .env file.")
    print("Please set your API key to proceed.")
    exit(1)


# ==============================================================================
# SECTION 3: INITIALIZE & CONFIGURE AGENT SYSTEM
# ==============================================================================

# Configure coordinator agent settings
configure_coordinator(
    OLLAMA_API_KEY,
    OLLAMA_BASE_URL,
    MODEL_NAME
)

# Configure specialist agents settings
configure_ollama(
    OLLAMA_API_KEY,
    OLLAMA_BASE_URL,
    MODEL_NAME
)


# ==============================================================================
# SECTION 4: INTERACTIVE REPL LOOP
# ==============================================================================

def main():
    """
    Main interactive loop for the V11 Multi-Agent System.
    Accepts complex user prompts, initiates multi-agent planning and execution,
    and displays the final aggregated answer.
    """
    # Display welcome header
    print("=" * 60)
    print("V11 - MULTI-AGENT SYSTEM")
    print("=" * 60)
    print()

    # Inform user of available agents and coordination behavior
    print("Available Specialist Agents:")
    print("1. File Agent       -> Directory and file management")
    print("2. Memory Agent     -> Long-term facts and knowledge retention")
    print("3. Calculator Agent -> Safe arithmetic calculations")
    print()
    print("The Coordinator Agent will analyze your prompt, decompose it into")
    print("steps, delegate each step to the right specialist, and synthesize")
    print("a complete final answer.")
    print()
    print("Type 'exit' to quit.\n")

    # Start user loop
    while True:
        try:
            # Capture user task input
            task = input("\nYou: ").strip()

        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C or EOF cleanly
            print("\nExiting...")
            break

        # Check for quit command
        if task.lower() == "exit":
            print("Goodbye!")
            break

        # Skip blank submissions
        if not task:
            continue

        try:
            # Execute multi-agent orchestration pipeline
            result = run_coordinator(task)

            # Display final synthesized answer
            print()
            print("=" * 60)
            print("FINAL SYNTHESIZED ANSWER")
            print("=" * 60)
            print()
            print(result)

        except Exception as error:
            # Gracefully handle and display runtime errors
            print()
            print("ERROR:")
            print(error)


# ==============================================================================
# SECTION 5: SCRIPT ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    main()