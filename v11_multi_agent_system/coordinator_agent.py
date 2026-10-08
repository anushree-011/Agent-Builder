"""
============================================================
V11 - COORDINATOR AGENT
============================================================

The Coordinator:

1. Receives the user task.
2. Creates an execution plan.
3. Selects specialist agents.
4. Executes them sequentially.
5. Stores their results in shared state.
6. Produces a final summary.
============================================================
"""

import json
import requests

from shared_state import SharedState

from agents import (
    SPECIALIST_AGENTS
)


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_API_KEY = None
OLLAMA_BASE_URL = None
MODEL_NAME = None


def configure_coordinator(
    api_key,
    base_url,
    model_name
):

    global OLLAMA_API_KEY
    global OLLAMA_BASE_URL
    global MODEL_NAME

    OLLAMA_API_KEY = api_key
    OLLAMA_BASE_URL = base_url
    MODEL_NAME = model_name


# ============================================================
# CALL OLLAMA
# ============================================================

def call_ollama(messages):

    url = f"{OLLAMA_BASE_URL}/chat"

    headers = {

        "Authorization":
            f"Bearer {OLLAMA_API_KEY}",

        "Content-Type":
            "application/json"
    }

    payload = {

        "model":
            MODEL_NAME,

        "messages":
            messages,

        "stream":
            False
    }

    response = requests.post(

        url,

        headers=headers,

        json=payload,

        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]


# ============================================================
# PARSE JSON
# ============================================================

def parse_json_response(response):

    response = response.strip()


    if response.startswith("```json"):

        response = response[7:]


    elif response.startswith("```"):

        response = response[3:]


    if response.endswith("```"):

        response = response[:-3]


    response = response.strip()


    try:

        return json.loads(response)

    except json.JSONDecodeError:

        print()
        print("Invalid Coordinator JSON:")

        print(response)

        return None


# ============================================================
# CREATE PLAN
# ============================================================

def create_plan(task):

    system_prompt = """
You are the Coordinator Agent.

Your job is to break a user task into steps
and decide which specialist agent should perform
each step.

Available agents:

FILE_AGENT
- Files and folders

MEMORY_AGENT
- Memory operations

CALCULATOR_AGENT
- Mathematical calculations

IMPORTANT:

A task can contain multiple steps.

Return ONLY JSON.

Format:

{
    "steps": [
        {
            "agent": "FILE_AGENT",
            "task": "Create a folder called V11_Project"
        },
        {
            "agent": "FILE_AGENT",
            "task": "Create README.md inside V11_Project"
        },
        {
            "agent": "MEMORY_AGENT",
            "task": "Remember that V11_Project was created"
        }
    ]
}

Rules:

1. Use only the available agents.
2. Put steps in the correct order.
3. If one step depends on another, put the dependency first.
4. Keep each task clear and specific.
5. Return only JSON.
"""


    messages = [

        {
            "role":
                "system",

            "content":
                system_prompt
        },

        {
            "role":
                "user",

            "content":
                task
        }
    ]


    response = call_ollama(
        messages
    )


    print()
    print("RAW COORDINATOR PLAN:")
    print(response)


    return parse_json_response(
        response
    )


# ============================================================
# EXECUTE PLAN
# ============================================================

def execute_plan(
    plan,
    shared_state
):

    if not plan:

        return "Coordinator could not create a valid plan."


    steps = plan.get(
        "steps",
        []
    )


    if not steps:

        return "Coordinator created an empty plan."


    print()
    print("=" * 60)
    print("EXECUTION PLAN")
    print("=" * 60)


    for index, step in enumerate(
        steps,
        start=1
    ):

        print()
        print(
            f"Step {index}"
        )

        print(
            f"Agent: {step.get('agent')}"
        )

        print(
            f"Task: {step.get('task')}"
        )


    # ========================================================
    # EXECUTE EACH STEP
    # ========================================================

    for index, step in enumerate(
        steps,
        start=1
    ):

        agent_name = step.get(
            "agent"
        )

        agent_task = step.get(
            "task"
        )


        print()
        print("=" * 60)

        print(
            f"EXECUTING STEP {index}"
        )

        print("=" * 60)


        if agent_name not in SPECIALIST_AGENTS:

            result = (
                f"Unknown agent: {agent_name}"
            )

            shared_state.add_result(
                agent_name,
                result
            )

            continue


        specialist = (
            SPECIALIST_AGENTS[
                agent_name
            ]
        )


        try:

            result = specialist(
                agent_task,
                shared_state
            )

        except Exception as error:

            result = (
                f"Agent execution error: {error}"
            )


        print()
        print(
            f"RESULT FROM {agent_name}:"
        )

        print(result)


        # ----------------------------------------------------
        # Save result in shared state
        # ----------------------------------------------------

        shared_state.add_result(
            agent_name,
            result
        )


        # ----------------------------------------------------
        # Display state after every step
        # ----------------------------------------------------

        shared_state.display()


    return "Plan execution completed."


# ============================================================
# FINAL SUMMARY
# ============================================================

def create_final_summary(
    task,
    shared_state
):

    results = (
        shared_state.get_results()
    )


    prompt = f"""
You are the Coordinator Agent.

The user originally requested:

{task}

The specialist agents completed these steps:

{results}

Create a short final response for the user.

Explain:

1. What was completed.
2. Which agents participated.
3. Important results.

Do not invent anything.
Only use the provided results.
"""


    messages = [

        {
            "role":
                "system",

            "content":
                "You summarize multi-agent work."
        },

        {
            "role":
                "user",

            "content":
                prompt
        }
    ]


    return call_ollama(
        messages
    )


# ============================================================
# RUN COORDINATOR
# ============================================================

def run_coordinator(task):

    # --------------------------------------------------------
    # Create shared state
    # --------------------------------------------------------

    shared_state = SharedState(
        task
    )


    print()
    print("=" * 60)
    print("V11 MULTI-AGENT SYSTEM")
    print("=" * 60)


    # --------------------------------------------------------
    # Create plan
    # --------------------------------------------------------

    plan = create_plan(
        task
    )


    # --------------------------------------------------------
    # Execute plan
    # --------------------------------------------------------

    execute_plan(
        plan,
        shared_state
    )


    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CREATING FINAL SUMMARY")
    print("=" * 60)


    final_answer = create_final_summary(
        task,
        shared_state
    )


    return final_answer