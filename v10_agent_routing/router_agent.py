"""
==============================================================================
V10 - AGENT ROUTING: ROUTER AGENT MODULE
==============================================================================
Concept & Architecture:
This module implements the "Router Agent" pattern in Agentic AI.
Instead of having a single monolithic agent try to do everything (file operations,
calculations, memory persistence, etc.), the Router Agent acts as an intelligent
traffic controller / dispatcher:
1. It analyzes the user's intent.
2. It classifies the task into one of the specialized agent categories.
3. It outputs a strictly formatted JSON decision.
4. It safely delegates execution to the selected specialist agent.

Key Topics Covered:
- Intent classification and classification prompting.
- Structured JSON outputs from LLMs.
- Code fence cleaning / markdown stripping.
- Graceful fallbacks and defensive agent routing.
- Delegation pattern to specialist agents.
==============================================================================
"""

# Import the standard JSON library for serializing and parsing structured responses
import json

# Import the requests library to send HTTP POST calls to the Ollama Cloud API endpoint
import requests


# ==============================================================================
# SECTION 1: GLOBAL CONFIGURATION STATE
# ==============================================================================
# These global variables store the credentials and connection parameters
# needed to communicate with the Ollama Cloud inference server.
# Initially set to None until explicitly configured by configure_router().
OLLAMA_API_KEY = None       # API token for authentication with Ollama Cloud
OLLAMA_BASE_URL = None      # Base URL (e.g., https://ollama.com/api)
MODEL_NAME = None           # Name of the LLM model (e.g., gemma4:31b)


def configure_router(api_key, base_url, model_name):
    """
    Configures the Router Agent with Ollama Cloud credentials.

    Parameters:
    -----------
    api_key : str
        The bearer authentication key required for API access.
    base_url : str
        The root API endpoint URL for Ollama Cloud service.
    model_name : str
        The identifier of the LLM to use for routing classification.
    """
    # Use global keyword so changes affect module-level variables
    global OLLAMA_API_KEY
    global OLLAMA_BASE_URL
    global MODEL_NAME

    # Assign passed configuration arguments to module globals
    OLLAMA_API_KEY = api_key
    OLLAMA_BASE_URL = base_url
    MODEL_NAME = model_name


# ==============================================================================
# SECTION 2: LLM API COMMUNICATION
# ==============================================================================
def call_ollama(messages):
    """
    Sends an HTTP request to the Ollama Cloud chat endpoint and extracts the text response.

    Parameters:
    -----------
    messages : list of dict
        A list of chat messages formatted as [{"role": "system"|"user", "content": "..."}].

    Returns:
    --------
    str : The raw text content of the assistant message returned by the model.
    """
    # Construct the full chat endpoint URL
    url = f"{OLLAMA_BASE_URL}/chat"

    # Define HTTP headers including Bearer authentication and JSON content type
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepare payload with model name, message history, and streaming disabled
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False  # Synchronous single-shot response
    }

    # Execute HTTP POST request with a 120-second timeout to handle large models
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

    # Raise an HTTPError if the response status code indicates an error (4xx or 5xx)
    response.raise_for_status()

    # Parse response body as JSON
    data = response.json()

    # Extract and return the assistant's message content string
    return data["message"]["content"]


# ==============================================================================
# SECTION 3: ROUTING CLASSIFICATION LOGIC
# ==============================================================================
def route_task(task):
    """
    Prompts the LLM to inspect the user's task and determine which specialist agent
    should handle it. Returns the agent identifier name as a string.

    Parameters:
    -----------
    task : str
        The natural language request input by the user.

    Returns:
    --------
    str : One of "FILE_AGENT", "MEMORY_AGENT", "CALCULATOR_AGENT", or "NONE".
    """
    # Define system prompt explaining the router's role, specialists, and strict output schema
    system_prompt = """
You are the Router Agent.

Your ONLY job is to decide which specialist agent
should handle the user's request.

Available specialist agents:

FILE_AGENT
- Create files
- Read files
- Create folders
- List files
- File and folder operations

MEMORY_AGENT
- Save memories
- Search memories
- Show memories

CALCULATOR_AGENT
- Mathematical calculations

IMPORTANT RULES:

1. Return ONLY a JSON object.
2. Do NOT use Markdown.
3. Strictly use this format: Do NOT wrap the output with ```json    ```
4. Do NOT add explanations.
5. The value of "agent" MUST be one of:
   FILE_AGENT
   MEMORY_AGENT
   CALCULATOR_AGENT
   NONE

Examples:

User:
Create a folder called Test

Response:
{"agent": "FILE_AGENT"}

User:
Remember that I am learning Agentic AI

Response:
{"agent": "MEMORY_AGENT"}

User:
Calculate 25 * 8

Response:
{"agent": "CALCULATOR_AGENT"}

User:
Tell me a joke

Response:
{"agent": "NONE"}
"""

    # Assemble conversation payload for the classification prompt
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

    # Query Ollama Cloud to get the routing classification
    response = call_ollama(messages)

    # Print raw response for debugging and transparency into agent reasoning
    print("\nRAW ROUTER RESPONSE:")
    print(response)

    # --------------------------------------------------------------------------
    # Defensive Parsing: Clean potential Markdown formatting
    # LLMs frequently wrap JSON in markdown blocks despite explicit negative instructions.
    # --------------------------------------------------------------------------
    response = response.strip()

    # Strip opening markdown code fence if present
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]

    # Strip closing markdown code fence if present
    if response.endswith("```"):
        response = response[:-3]

    # Re-trim leading/trailing whitespace after removing fences
    response = response.strip()

    # --------------------------------------------------------------------------
    # Validate and Parse JSON
    # --------------------------------------------------------------------------
    try:
        # Parse the cleaned text into a dictionary
        decision = json.loads(response)

        # Retrieve the 'agent' field, defaulting to "NONE" if missing
        agent_name = decision.get("agent", "NONE")

        # Set of valid, permitted specialist identifiers
        allowed_agents = {
            "FILE_AGENT",
            "MEMORY_AGENT",
            "CALCULATOR_AGENT",
            "NONE"
        }

        # Guard against hallucinated agent names
        if agent_name not in allowed_agents:
            print("\nUnknown agent returned by Router.")
            return "NONE"

        return agent_name

    except json.JSONDecodeError:
        # Handle cases where model failed to output parseable JSON
        print("\nRouter returned invalid JSON.")
        print("Cleaned response:")
        print(response)
        return "NONE"


# ==============================================================================
# SECTION 4: ROUTER EXECUTION & DELEGATION PIPELINE
# ==============================================================================
def run_router(task):
    """
    Executes the full routing lifecycle:
    1. Display task.
    2. Route task to specialist agent.
    3. Import specialist registry dynamically.
    4. Delegate task to the selected specialist agent.
    5. Return the specialist's result.

    Parameters:
    -----------
    task : str
        The input request from the user.

    Returns:
    --------
    str : Output or error message from the selected specialist agent.
    """
    # Display visual banner for task execution
    print()
    print("=" * 60)
    print("USER TASK:")
    print(task)
    print("=" * 60)

    # STEP 1: Router classifies user intent
    selected_agent = route_task(task)

    # Display routing result
    print()
    print("ROUTER DECISION:")
    print(selected_agent)

    # STEP 2: Import specialist agents dictionary lazily to avoid circular imports
    from specialist_agents import SPECIALIST_AGENTS

    # STEP 3: Verify if selected specialist agent is mapped in the registry
    if selected_agent not in SPECIALIST_AGENTS:
        return "No suitable specialist agent found."

    # STEP 4: Retrieve the specialist handler function
    specialist = SPECIALIST_AGENTS[selected_agent]

    print()
    print("DELEGATING TO:")
    print(selected_agent)

    # STEP 5: Dispatch user task to the chosen specialist agent and return result
    result = specialist(task)

    return result