"""
============================================================
V11 - MULTI-AGENT SYSTEM
============================================================
"""

import os

from dotenv import load_dotenv

from coordinator_agent import (
    configure_coordinator,
    run_coordinator
)

from agents import (
    configure_ollama
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY"
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemma4:31b"
)


# ============================================================
# CHECK API KEY
# ============================================================

if not OLLAMA_API_KEY:

    print(
        "ERROR: OLLAMA_API_KEY is missing."
    )

    exit()


# ============================================================
# CONFIGURE AGENTS
# ============================================================

configure_coordinator(

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
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        "V11 - MULTI-AGENT SYSTEM"
    )

    print("=" * 60)

    print()

    print(
        "Available Agents:"
    )

    print(
        "1. File Agent"
    )

    print(
        "2. Memory Agent"
    )

    print(
        "3. Calculator Agent"
    )

    print()

    print(
        "The Coordinator Agent will decide"
    )

    print(
        "which agents are needed."
    )

    print()

    print(
        "Type 'exit' to stop."
    )


    while True:

        try:

            task = input(
                "\nYou: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()
            print(
                "Exiting..."
            )

            break


        if task.lower() == "exit":

            print(
                "Goodbye!"
            )

            break


        if not task:

            continue


        try:

            result = run_coordinator(
                task
            )


            print()
            print("=" * 60)

            print(
                "FINAL ANSWER"
            )

            print("=" * 60)

            print()

            print(result)


        except Exception as error:

            print()
            print(
                "ERROR:"
            )

            print(error)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()