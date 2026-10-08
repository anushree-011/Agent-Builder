import json
import requests


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_API_KEY = None
OLLAMA_BASE_URL = None
MODEL_NAME = None


def configure_router(api_key, base_url, model_name):
    """
    Store the Ollama configuration used by the Router Agent.
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
    Send a request to Ollama Cloud and return the model response.
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
# ROUTER AGENT
# ============================================================

def route_task(task):
    """
    Ask the Router Agent which specialist should handle
    the user's task.
    """

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

    # --------------------------------------------------------
    # Ask Ollama
    # --------------------------------------------------------

    response = call_ollama(messages)

    # --------------------------------------------------------
    # DEBUG
    #
    # This lets us see exactly what the Router Agent returned.
    # --------------------------------------------------------

    print("\nRAW ROUTER RESPONSE:")
    print(response)

    # --------------------------------------------------------
    # Clean the response
    #
    # Sometimes an LLM returns:
    #
    # ```json
    # {"agent": "CALCULATOR_AGENT"}
    # ```
    #
    # We remove the Markdown code fences if they appear.
    # --------------------------------------------------------

    response = response.strip()

    if response.startswith("```json"):

        response = response[7:]

    elif response.startswith("```"):

        response = response[3:]

    if response.endswith("```"):

        response = response[:-3]

    response = response.strip()

    # --------------------------------------------------------
    # Convert response to JSON
    # --------------------------------------------------------

    try:

        decision = json.loads(response)

        agent_name = decision.get(
            "agent",
            "NONE"
        )

        # ----------------------------------------------------
        # Safety check
        #
        # Only allow known specialist agents.
        # ----------------------------------------------------

        allowed_agents = {
            "FILE_AGENT",
            "MEMORY_AGENT",
            "CALCULATOR_AGENT",
            "NONE"
        }

        if agent_name not in allowed_agents:

            print(
                "\nUnknown agent returned by Router."
            )

            return "NONE"

        return agent_name

    except json.JSONDecodeError:

        print(
            "\nRouter returned invalid JSON."
        )

        print(
            "Cleaned response:"
        )

        print(response)

        return "NONE"


# ============================================================
# RUN ROUTER
# ============================================================

def run_router(task):
    """
    Run the complete routing process.

    Flow:

    User Task
        ↓
    Router Agent
        ↓
    Specialist Agent
    """

    print()
    print("=" * 60)

    print("USER TASK:")
    print(task)

    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1 - Router decides
    # --------------------------------------------------------

    selected_agent = route_task(task)

    print()
    print("ROUTER DECISION:")
    print(selected_agent)

    # --------------------------------------------------------
    # STEP 2 - Import specialist agents
    # --------------------------------------------------------

    from specialist_agents import SPECIALIST_AGENTS

    # --------------------------------------------------------
    # STEP 3 - Check whether a specialist exists
    # --------------------------------------------------------

    if selected_agent not in SPECIALIST_AGENTS:

        return "No suitable specialist agent found."

    # --------------------------------------------------------
    # STEP 4 - Select specialist
    # --------------------------------------------------------

    specialist = SPECIALIST_AGENTS[selected_agent]

    print()
    print("DELEGATING TO:")
    print(selected_agent)

    # --------------------------------------------------------
    # STEP 5 - Give the task to specialist
    # --------------------------------------------------------

    result = specialist(task)

    return result