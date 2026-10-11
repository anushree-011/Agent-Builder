"""
==============================================================================
V11 - MULTI-AGENT SYSTEM: SPECIALIST AGENTS MODULE
==============================================================================
Concept & Architecture:
This module contains the domain-specific "Specialist Agents" designed to work in a
collaborative Multi-Agent System (MAS).

Unlike standalone agents, each specialist in this version accepts TWO inputs:
1. `task` : The specific subtask assigned by the coordinator.
2. `shared_state` : The live blackboard holding previous results from all other agents.

This allows agents to make context-aware decisions. For instance:
- If File Agent created a folder named "V11_Project",
- Memory Agent can read that from `shared_state` and save a memory confirming it,
- Without needing hardcoded parameters passed manually by a human!

Specialists Included:
- FILE_AGENT: File and directory manipulation.
- MEMORY_AGENT: Short/long-term factual storage and retrieval.
- CALCULATOR_AGENT: Safe mathematical evaluation via AST.
==============================================================================
"""

# Import json for decoding LLM tool invocation decisions
import json

# Import requests for making HTTP calls to Ollama Cloud
import requests

# Import the actual tool functions from tools module
from tools import (
    list_files,      # Directory listing
    read_file,       # File reading
    create_folder,   # Folder creation
    create_file,     # File creation and writing
    save_memory,     # Append to in-memory fact list
    search_memory,   # Keyword search over memories
    show_memories,   # List all stored memories
    calculate        # Safe AST arithmetic evaluator
)


# ==============================================================================
# SECTION 1: GLOBAL CONFIGURATION
# ==============================================================================
# Connection settings for specialist agent inference
OLLAMA_API_KEY = None       # API token for Ollama Cloud
OLLAMA_BASE_URL = None      # Ollama API root endpoint
MODEL_NAME = None           # LLM model identifier


def configure_ollama(api_key, base_url, model_name):
    """
    Configures API credentials for all specialist agents in the multi-agent system.

    Parameters:
    -----------
    api_key : str
        The bearer authentication key required for API access.
    base_url : str
        The root API endpoint URL for Ollama Cloud service.
    model_name : str
        The identifier of the LLM to use for specialist inference.
    """
    # Use global keyword to modify module-level variables
    global OLLAMA_API_KEY
    global OLLAMA_BASE_URL
    global MODEL_NAME

    # Assign configuration parameters
    OLLAMA_API_KEY = api_key
    OLLAMA_BASE_URL = base_url
    MODEL_NAME = model_name


# ==============================================================================
# SECTION 2: API DISPATCHER
# ==============================================================================
def call_ollama(messages):
    """
    Dispatches chat messages to Ollama Cloud and returns the response string.

    Parameters:
    -----------
    messages : list of dict
        Message sequence [{"role": "system"|"user", "content": "..."}].

    Returns:
    --------
    str : Raw text response produced by the model.
    """
    # Build endpoint URL
    url = f"{OLLAMA_BASE_URL}/chat"

    # Define request headers
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepare JSON payload
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False  # Non-streaming request
    }

    # Execute HTTP POST call with 120-second timeout
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

    # Raise exception if request failed
    response.raise_for_status()

    # Parse JSON response body
    data = response.json()

    # Extract text content
    return data["message"]["content"]


# ==============================================================================
# SECTION 3: ROBUST JSON PARSER
# ==============================================================================
def parse_json_response(response):
    """
    Extracts and parses JSON from model responses, stripping markdown code fences.

    Parameters:
    -----------
    response : str
        Raw string output from LLM.

    Returns:
    --------
    dict or None : Parsed JSON dictionary or None if decoding failed.
    """
    # Strip whitespace
    response = response.strip()

    # Strip opening markdown code fence
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]

    # Strip closing markdown code fence
    if response.endswith("```"):
        response = response[:-3]

    # Re-trim whitespace
    response = response.strip()

    # Decode JSON string
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        print()
        print("Invalid JSON returned by agent:")
        print(response)
        return None


# ==============================================================================
# SECTION 4: FILE SPECIALIST AGENT (AWARE OF SHARED STATE)
# ==============================================================================
def file_agent(task, shared_state):
    """
    Specialist agent for handling file and folder operations within multi-agent flows.

    Parameters:
    -----------
    task : str
        The assigned file subtask.
    shared_state : SharedState
        The shared state containing prior actions from other agents.

    Returns:
    --------
    str : Outcome of the executed file tool.
    """
    # Constrained system prompt for file operations
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

    # Retrieve prior agent accomplishments from the shared blackboard
    previous_results = shared_state.get_results()

    # Build prompt providing both the assigned task AND previous results
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
Original Task:

{task}

Previous agent results:

{previous_results}

Decide which file tool should be used.
"""
        }
    ]

    # Query LLM
    response = call_ollama(messages)

    # Print raw response for debugging
    print()
    print("FILE AGENT RESPONSE:")
    print(response)

    # Clean and parse decision JSON
    decision = parse_json_response(response)

    # Validate parsing
    if decision is None:
        return "File Agent returned invalid JSON."

    # Extract tool name and arguments dictionary
    tool = decision.get("tool")
    arguments = decision.get("arguments", {})

    # Execute corresponding tool
    if tool == "list_files":
        return list_files(**arguments)
    elif tool == "read_file":
        return read_file(**arguments)
    elif tool == "create_folder":
        return create_folder(**arguments)
    elif tool == "create_file":
        return create_file(**arguments)

    return "File Agent could not determine a valid tool."


# ==============================================================================
# SECTION 5: MEMORY SPECIALIST AGENT (AWARE OF SHARED STATE)
# ==============================================================================
def memory_agent(task, shared_state):
    """
    Specialist agent for memory recording and retrieval within multi-agent flows.

    Parameters:
    -----------
    task : str
        The assigned memory subtask.
    shared_state : SharedState
        The shared state containing prior actions from other agents.

    Returns:
    --------
    str : Outcome of the executed memory tool.
    """
    # Constrained system prompt exposing only memory tools
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

    # Read previous agent outputs from shared state
    previous_results = shared_state.get_results()

    # Construct messages with historical context
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
Original Task:

{task}

Previous agent results:

{previous_results}

Decide which memory tool should be used.
"""
        }
    ]

    # Query LLM
    response = call_ollama(messages)

    # Print raw response
    print()
    print("MEMORY AGENT RESPONSE:")
    print(response)

    # Parse JSON
    decision = parse_json_response(response)

    # Validate parsing
    if decision is None:
        return "Memory Agent returned invalid JSON."

    # Extract tool and arguments
    tool = decision.get("tool")
    arguments = decision.get("arguments", {})

    # Dispatch tool
    if tool == "save_memory":
        return save_memory(**arguments)
    elif tool == "search_memory":
        return search_memory(**arguments)
    elif tool == "show_memories":
        return show_memories()

    return "Memory Agent could not determine a valid tool."


# ==============================================================================
# SECTION 6: CALCULATOR SPECIALIST AGENT (AWARE OF SHARED STATE)
# ==============================================================================
def calculator_agent(task, shared_state):
    """
    Specialist agent for mathematical evaluations within multi-agent flows.

    Parameters:
    -----------
    task : str
        The assigned mathematical subtask.
    shared_state : SharedState
        The shared state containing prior actions from other agents.

    Returns:
    --------
    str : Result of the arithmetic evaluation.
    """
    # Constrained system prompt for calculator
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

    # Retrieve prior steps from shared blackboard
    previous_results = shared_state.get_results()

    # Assemble messages with historical state
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
Original Task:

{task}

Previous agent results:

{previous_results}

Perform the required calculation.
"""
        }
    ]

    # Query LLM
    response = call_ollama(messages)

    # Print raw response
    print()
    print("CALCULATOR AGENT RESPONSE:")
    print(response)

    # Parse JSON
    decision = parse_json_response(response)

    # Validate parsing
    if decision is None:
        return "Calculator Agent returned invalid JSON."

    # Extract tool and arguments
    tool = decision.get("tool")
    arguments = decision.get("arguments", {})

    # Dispatch calculation tool
    if tool == "calculate":
        return calculate(**arguments)

    return "Calculator Agent could not determine a valid calculation."


# ==============================================================================
# SECTION 7: SPECIALIST AGENT REGISTRY MAP
# ==============================================================================
# Maps agent identifier strings in Coordinator plans to callable agent functions
SPECIALIST_AGENTS = {
    "FILE_AGENT": file_agent,
    "MEMORY_AGENT": memory_agent,
    "CALCULATOR_AGENT": calculator_agent
}