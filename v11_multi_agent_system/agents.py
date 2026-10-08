"""
============================================================
V11 - SPECIALIST AGENTS
============================================================

Specialist agents:

1. File Agent
2. Memory Agent
3. Calculator Agent

Each agent can receive shared state and return a result.
============================================================
"""

import json
import requests

from tools import (
    list_files,
    read_file,
    create_folder,
    create_file,
    save_memory,
    search_memory,
    show_memories,
    calculate
)


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_API_KEY = None
OLLAMA_BASE_URL = None
MODEL_NAME = None


def configure_ollama(
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
# PARSE JSON RESPONSE
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
        print("Invalid JSON returned by agent:")

        print(response)

        return None


# ============================================================
# FILE AGENT
# ============================================================

def file_agent(task, shared_state):

    system_prompt = """
You are the File Specialist Agent.

Your job is to perform file and folder operations.

Available tools:

list_files(path)

read_file(path)

create_folder(path)

create_file(path, content)

Return ONLY JSON.

Do not use Markdown.

Example:

{
    "tool": "create_folder",
    "arguments": {
        "path": "V11_Project"
    }
}

Example:

{
    "tool": "create_file",
    "arguments": {
        "path": "V11_Project/README.md",
        "content": "Learning Multi-Agent Systems"
    }
}
"""


    # Include previous results
    previous_results = shared_state.get_results()


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
                f"""
Original Task:

{task}

Previous agent results:

{previous_results}

Decide which file tool should be used.
"""
        }
    ]


    response = call_ollama(
        messages
    )


    print()
    print("FILE AGENT RESPONSE:")
    print(response)


    decision = parse_json_response(
        response
    )


    if decision is None:

        return "File Agent returned invalid JSON."


    tool = decision.get(
        "tool"
    )

    arguments = decision.get(
        "arguments",
        {}
    )


    if tool == "list_files":

        return list_files(
            **arguments
        )


    elif tool == "read_file":

        return read_file(
            **arguments
        )


    elif tool == "create_folder":

        return create_folder(
            **arguments
        )


    elif tool == "create_file":

        return create_file(
            **arguments
        )


    return "File Agent could not determine a valid tool."


# ============================================================
# MEMORY AGENT
# ============================================================

def memory_agent(task, shared_state):

    system_prompt = """
You are the Memory Specialist Agent.

Your job is to handle memory operations.

Available tools:

save_memory(text)

search_memory(keyword)

show_memories()

Return ONLY JSON.

Do not use Markdown.

Example:

{
    "tool": "save_memory",
    "arguments": {
        "text": "The V11 project was created."
    }
}
"""


    previous_results = (
        shared_state.get_results()
    )


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
                f"""
Original Task:

{task}

Previous agent results:

{previous_results}

Decide which memory tool should be used.
"""
        }
    ]


    response = call_ollama(
        messages
    )


    print()
    print("MEMORY AGENT RESPONSE:")
    print(response)


    decision = parse_json_response(
        response
    )


    if decision is None:

        return "Memory Agent returned invalid JSON."


    tool = decision.get(
        "tool"
    )

    arguments = decision.get(
        "arguments",
        {}
    )


    if tool == "save_memory":

        return save_memory(
            **arguments
        )


    elif tool == "search_memory":

        return search_memory(
            **arguments
        )


    elif tool == "show_memories":

        return show_memories()


    return "Memory Agent could not determine a valid tool."


# ============================================================
# CALCULATOR AGENT
# ============================================================

def calculator_agent(task, shared_state):

    system_prompt = """
You are the Calculator Specialist Agent.

Your job is to perform mathematical calculations.

Available tool:

calculate(expression)

Return ONLY JSON.

Do not use Markdown.

Example:

{
    "tool": "calculate",
    "arguments": {
        "expression": "25 * 8"
    }
}
"""


    previous_results = (
        shared_state.get_results()
    )


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
                f"""
Original Task:

{task}

Previous agent results:

{previous_results}

Perform the required calculation.
"""
        }
    ]


    response = call_ollama(
        messages
    )


    print()
    print("CALCULATOR AGENT RESPONSE:")
    print(response)


    decision = parse_json_response(
        response
    )


    if decision is None:

        return "Calculator Agent returned invalid JSON."


    tool = decision.get(
        "tool"
    )

    arguments = decision.get(
        "arguments",
        {}
    )


    if tool == "calculate":

        return calculate(
            **arguments
        )


    return (
        "Calculator Agent could not "
        "determine a valid calculation."
    )


# ============================================================
# SPECIALIST AGENT MAP
# ============================================================

SPECIALIST_AGENTS = {

    "FILE_AGENT":
        file_agent,

    "MEMORY_AGENT":
        memory_agent,

    "CALCULATOR_AGENT":
        calculator_agent
}