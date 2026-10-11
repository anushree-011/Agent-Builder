"""
==============================================================================
V10 - AGENT ROUTING: MAIN ENTRY POINT
==============================================================================
Concept & Purpose:
This script serves as the interactive Command Line Interface (CLI) for Version 10.
It initializes environment variables, configures the Router Agent and Specialist
Agents with credentials, and runs an interactive REPL loop where the user can submit
tasks to observe intelligent agent routing in real-time.

Execution:
python main.py
==============================================================================
"""

# Import os module for reading system environment variables
import os

# Import load_dotenv to load settings from local .env file
from dotenv import load_dotenv

# Import router configuration and runner from router_agent module
from router_agent import (
    configure_router,   # Sets API credentials for the router
    run_router          # Runs the router-to-specialist execution pipeline
)

# Import specialist agent configuration from specialist_agents module
from specialist_agents import configure_ollama


# ==============================================================================
# SECTION 1: LOAD ENVIRONMENT CONFIGURATION
# ==============================================================================

# Read key-value pairs from .env into os.environ
load_dotenv()

# Retrieve Ollama Cloud API Key
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Retrieve Ollama API Base URL, defaulting to the official cloud endpoint
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)

# Retrieve LLM Model Name, defaulting to gemma4:31b
MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemma4:31b"
)


# ==============================================================================
# SECTION 2: ENVIRONMENT VALIDATION
# ==============================================================================

# Ensure the required API key exists before proceeding
if not OLLAMA_API_KEY:
    print("ERROR: OLLAMA_API_KEY is missing from .env file.")
    print("Please add your key to continue.")
    exit(1)


# ==============================================================================
# SECTION 3: INITIALIZE AND CONFIGURE AGENTS
# ==============================================================================

# Provide credentials to the Router Agent
configure_router(
    OLLAMA_API_KEY,
    OLLAMA_BASE_URL,
    MODEL_NAME
)

# Provide credentials to the Specialist Agents
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
    Main interactive loop for the V10 Agent Routing system.
    Prompts the user for queries, delegates them through the router, and prints results.
    """
    # Display welcome banner
    print("=" * 60)
    print("V10 - AGENT ROUTING SYSTEM")
    print("=" * 60)

    # Display available specialists to the user
    print("\nAvailable Specialist Agents:")
    print("1. File Agent       -> Files and directory tasks")
    print("2. Memory Agent     -> Storing and searching facts")
    print("3. Calculator Agent -> Arithmetic computations")

    print("\nType 'exit' to quit.\n")

    # Start continuous loop
    while True:
        try:
            # Capture user input from the terminal
            task = input("\nYou: ").strip()

        except (KeyboardInterrupt, EOFError):
            # Gracefully handle Ctrl+C or end-of-file signal
            print("\nExiting...")
            break

        # Check for exit command
        if task.lower() == "exit":
            print("Goodbye!")
            break

        # Skip empty inputs
        if not task:
            continue

        try:
            # Execute routing pipeline: Intent detection -> Specialist delegation -> Tool execution
            result = run_router(task)

            # Print the final output returned by the delegated specialist
            print("\nFINAL RESULT:")
            print(result)

        except Exception as e:
            # Catch and display any runtime errors without crashing the session
            print("\nERROR:")
            print(e)


# ==============================================================================
# SECTION 5: SCRIPT ENTRY POINT
# ==============================================================================

# Execute main() only when run directly as a script
if __name__ == "__main__":
    main()