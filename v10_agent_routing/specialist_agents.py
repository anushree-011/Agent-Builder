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


def configure_ollama(api_key, base_url, model_name):
    """
    Store Ollama configuration for the specialist agents.
    """

    global OLLAMA_API_KEY
    global OLLAMA_BASE_URL
    global MODEL_NAME

    OLLAMA_API_KEY = api_key
    OLLAMA_BASE_URL = base_url
    MODEL_NAME = model_name


# ============================================================
# CALL OLLAMA CLOUD
# ============================================================

def call_ollama(messages):
    """
    Send a request to Ollama Cloud.
    """

    url = f"{OLLAMA_BASE_URL}/chat"

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
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
# PARSE SPECIALIST RESPONSE
# ============================================================

def parse_tool_response(response):
    """
    Convert the specialist agent's response into JSON.

    The model may return either:

    {
        "tool": "calculate",
        "arguments": {
            "expression": "25 * 8"
        }
    }

    OR it may incorrectly wrap it in Markdown:

    ```json
    {
        "tool": "calculate",
        "arguments": {
            "expression": "25 * 8"
        }
    }
    ```

    This function handles both cases.
    """

    response = response.strip()

    # --------------------------------------------------------
    # Remove Markdown code fences
    # --------------------------------------------------------

    if response.startswith("```json"):

        response = response[7:]

    elif response.startswith("```"):

        response = response[3:]

    if response.endswith("```"):

        response = response[:-3]

    response = response.strip()

    # --------------------------------------------------------
    # Convert JSON text into Python dictionary
    # --------------------------------------------------------

    try:

        return json.loads(response)

    except json.JSONDecodeError:

        print("\nSPECIALIST RETURNED INVALID JSON:")
        print(response)

        return None


# ============================================================
# FILE AGENT
# ============================================================

def file_agent(task):
    """
    Specialist agent responsible for file operations.
    """

    system_prompt = """
You are the File Specialist Agent.

Your job is to handle file and folder related tasks.

Available tools:

1. list_files(path)
2. read_file(path)
3. create_folder(path)
4. create_file(path, content)

IMPORTANT:

Return ONLY JSON.

Do NOT use Markdown.
Do NOT use ```json.
Do NOT add explanations.

Examples:

Create a folder called Test:

{
    "tool": "create_folder",
    "arguments": {
        "path": "Test"
    }
}

Read a file:

{
    "tool": "read_file",
    "arguments": {
        "path": "test.txt"
    }
}

Create a file:

{
    "tool": "create_file",
    "arguments": {
        "path": "test.txt",
        "content": "Hello"
    }
}

List files:

{
    "tool": "list_files",
    "arguments": {
        "path": "."
    }
}

If no tool is appropriate:

{
    "tool": "none",
    "arguments": {}
}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": task
        }
    ]

    response = call_ollama(messages)

    print("\nRAW FILE AGENT RESPONSE:")
    print(response)

    decision = parse_tool_response(response)

    if decision is None:
        return "File Agent returned an invalid response."

    tool = decision.get("tool")
    arguments = decision.get("arguments", {})

    # --------------------------------------------------------
    # Execute selected tool
    # --------------------------------------------------------

    if tool == "list_files":

        return list_files(**arguments)

    elif tool == "read_file":

        return read_file(**arguments)

    elif tool == "create_folder":

        return create_folder(**arguments)

    elif tool == "create_file":

        return create_file(**arguments)

    else:

        return "File Agent could not determine a valid tool."


# ============================================================
# MEMORY AGENT
# ============================================================

def memory_agent(task):
    """
    Specialist agent responsible for memory operations.
    """

    system_prompt = """
You are the Memory Specialist Agent.

Your job is to handle memory-related tasks.

Available tools:

1. save_memory(text)
2. search_memory(keyword)
3. show_memories()

IMPORTANT:

Return ONLY JSON.

Do NOT use Markdown.
Do NOT use ```json.
Do NOT add explanations.

Examples:

Save a memory:

{
    "tool": "save_memory",
    "arguments": {
        "text": "The user is learning Agentic AI."
    }
}

Search memory:

{
    "tool": "search_memory",
    "arguments": {
        "keyword": "Agentic AI"
    }
}

Show memories:

{
    "tool": "show_memories",
    "arguments": {}
}

If no tool is appropriate:

{
    "tool": "none",
    "arguments": {}
}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": task
        }
    ]

    response = call_ollama(messages)

    print("\nRAW MEMORY AGENT RESPONSE:")
    print(response)

    decision = parse_tool_response(response)

    if decision is None:
        return "Memory Agent returned an invalid response."

    tool = decision.get("tool")
    arguments = decision.get("arguments", {})

    # --------------------------------------------------------
    # Execute selected tool
    # --------------------------------------------------------

    if tool == "save_memory":

        return save_memory(**arguments)

    elif tool == "search_memory":

        return search_memory(**arguments)

    elif tool == "show_memories":

        return show_memories()

    else:

        return "Memory Agent could not determine a valid tool."


# ============================================================
# CALCULATOR AGENT
# ============================================================

def calculator_agent(task):
    """
    Specialist agent responsible for calculations.
    """

    system_prompt = """
You are the Calculator Specialist Agent.

Your job is to handle mathematical calculations.

You have one tool:

calculate(expression)

IMPORTANT:

Return ONLY JSON.

Do NOT use Markdown.
Do NOT use ```json.
Do NOT add explanations.

Example:

User:
Calculate 25 * 8

Response:

{
    "tool": "calculate",
    "arguments": {
        "expression": "25 * 8"
    }
    }
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": task
        }
    ]

    response = call_ollama(messages)

    print("\nRAW CALCULATOR AGENT RESPONSE:")
    print(response)

    decision = parse_tool_response(response)

    if decision is None:
        return "Calculator Agent returned an invalid response."

    tool = decision.get("tool")
    arguments = decision.get("arguments", {})

    # --------------------------------------------------------
    # Execute calculator tool
    # --------------------------------------------------------

    if tool == "calculate":

        return calculate(**arguments)

    else:

        return "Calculator Agent could not determine a valid tool."


# ============================================================
# SPECIALIST AGENT MAP
# ============================================================

SPECIALIST_AGENTS = {

    "FILE_AGENT": file_agent,

    "MEMORY_AGENT": memory_agent,

    "CALCULATOR_AGENT": calculator_agent

}