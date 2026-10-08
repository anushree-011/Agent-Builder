import os

from dotenv import load_dotenv

from router_agent import (
    configure_router,
    run_router
)

from specialist_agents import configure_ollama


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

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


# ============================================================
# CHECK CONFIGURATION
# ============================================================

if not OLLAMA_API_KEY:

    print("ERROR: OLLAMA_API_KEY is missing.")

    exit()


# ============================================================
# CONFIGURE AGENTS
# ============================================================

configure_router(
    OLLAMA_API_KEY,
    OLLAMA_BASE_URL,
    MODEL_NAME
)

configure_ollama(
    OLLAMA_API_KEY,
    OLLAMA_BASE_URL,
    MODEL_NAME
)


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 60)
    print("V10 - AGENT ROUTING SYSTEM")
    print("=" * 60)

    print("\nAvailable Specialist Agents:")

    print("1. File Agent")
    print("2. Memory Agent")
    print("3. Calculator Agent")

    print("\nType 'exit' to quit.")

    while True:

        try:

            task = input("\nYou: ").strip()

        except (KeyboardInterrupt, EOFError):

            print("\nExiting...")

            break

        if task.lower() == "exit":

            print("Goodbye!")

            break

        if not task:

            continue

        try:

            result = run_router(task)

            print("\nFINAL RESULT:")
            print(result)

        except Exception as e:

            print("\nERROR:")
            print(e)


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()