import os
import json
import time
import requests
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# MODEL AND API CONFIGURATION
# ============================================================

MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:31b")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)


# ============================================================
# V4 — PLANNING AGENT
# ============================================================
#
# V1 → Chat agent
# V2 → Read-only file agent
# V3 → File creation agent
# V4 → Planning agent
#
# V4 introduces:
#
# 1. Planning
# 2. Task decomposition
# 3. Sequential execution
# 4. Task status tracking
# 5. Tool execution
# 6. Final result reporting
#
# ============================================================


# ============================================================
# CONCEPT 1: FILE TOOLS
# ============================================================


def list_files(directory: str = ".") -> str:
    """Lists all files and folders inside a directory."""

    try:
        items = os.listdir(directory)

        if not items:
            return f"The directory '{directory}' is empty."

        result = f"Contents of '{directory}':\n"

        for item in items:
            full_path = os.path.join(directory, item)

            if os.path.isdir(full_path):
                kind = "FOLDER"
            else:
                kind = "FILE"

            result += f"  {kind}: {item}\n"

        return result

    except FileNotFoundError:
        return f"Error: Directory '{directory}' not found."

    except PermissionError:
        return f"Error: Permission denied to read '{directory}'."

    except Exception as e:
        return f"Error listing directory: {e}"


def read_file(filepath: str) -> str:
    """Reads the text content of a file."""

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) > 3000:
            return (
                content[:3000]
                + "\n\n[...File truncated for length...]"
            )

        return content

    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."

    except Exception as e:
        return f"Error reading file: {e}"


def create_folder(folder_path: str) -> str:
    """Creates a folder and any required parent folders."""

    try:
        os.makedirs(folder_path, exist_ok=True)

        return (
            f"Success: Folder '{folder_path}' "
            f"created successfully."
        )

    except Exception as e:
        return (
            f"Error creating folder "
            f"'{folder_path}': {e}"
        )


def create_file(filepath: str, content: str = "") -> str:
    """Creates a file with the specified content."""

    try:

        # Create parent directory if necessary
        parent_dir = os.path.dirname(filepath)

        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # Create/write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return (
            f"Success: File '{filepath}' "
            f"created successfully "
            f"({len(content)} characters written)."
        )

    except Exception as e:
        return (
            f"Error creating file "
            f"'{filepath}': {e}"
        )


# ============================================================
# TOOL SCHEMAS
# ============================================================

ALL_TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "Lists all files and folders inside "
                "a given directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": (
                            "Directory path to list. "
                            "Defaults to current directory."
                        )
                    }
                }
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Reads the text content of an existing file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file."
                    }
                },
                "required": ["filepath"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": (
                "Creates a folder and any necessary "
                "parent folders."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": (
                            "Path of the folder to create."
                        )
                    }
                },
                "required": ["folder_path"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": (
                "Creates a file at the specified path "
                "with the specified content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": (
                            "Target file path."
                        )
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "Text content to write "
                            "inside the file."
                        )
                    }
                },
                "required": ["filepath"]
            }
        }
    }

]


# ============================================================
# TOOL MAP
# ============================================================

TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
    "create_folder": create_folder,
    "create_file": create_file,
}


# ============================================================
# CONCEPT 2: CALL OLLAMA
# ============================================================


def call_ollama(messages, tools=None):

    """Send a chat request to Ollama Cloud."""

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    if tools:
        payload["tools"] = tools

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3

    for attempt in range(max_retries + 1):

        try:

            response = requests.post(
                f"{OLLAMA_BASE_URL}/chat",
                json=payload,
                headers=headers,
                timeout=120
            )

            response.raise_for_status()

            return response.json()

        except Exception as e:

            error_text = str(e).lower()

            if (
                attempt < max_retries
                and (
                    "503" in str(e)
                    or "504" in str(e)
                    or "timeout" in error_text
                )
            ):

                wait = 2 ** (attempt + 1)

                print(
                    f"  Model busy. "
                    f"Retrying in {wait}s..."
                )

                time.sleep(wait)

            else:
                raise


# ============================================================
# CONCEPT 3: CREATE PLAN
# ============================================================


def create_plan(task: str) -> str:
    """
    Ask the model to break the user's task
    into clear sequential steps.
    """

    planning_messages = [

        {
            "role": "system",
            "content": """
You are a planning agent.

Your job is to break the user's task into
clear, logical, sequential steps.

Rules:

1. Analyze the complete task first.
2. Break multi-step tasks into smaller steps.
3. Number every step.
4. Keep steps simple and actionable.
5. Do not execute tools during planning.
6. The plan should describe WHAT needs to happen,
   not perform the actions.

Example:

User:
Create a project folder and inside it create
README.md and notes/todo.txt.

Plan:

1. Create the project folder.
2. Create README.md inside the project folder.
3. Create the notes folder.
4. Create todo.txt inside the notes folder.
5. Verify the created files.
"""
        },

        {
            "role": "user",
            "content": task
        }

    ]

    data = call_ollama(planning_messages)

    return data["message"].get("content", "")


# ============================================================
# CONCEPT 4: AGENTIC EXECUTION LOOP
# ============================================================


def run_agent(task: str, system_context: str) -> str:
    """
    Creates a plan first and then executes the task
    using the available tools.
    """

    # --------------------------------------------------------
    # STEP 1 — CREATE PLAN
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("CREATING PLAN")
    print("=" * 60)

    plan = create_plan(task)

    print("\nPLAN:")
    print(plan)

    print("\n" + "=" * 60)
    print("EXECUTING PLAN")
    print("=" * 60)

    # --------------------------------------------------------
    # STEP 2 — SEND PLAN + TASK TO EXECUTION AGENT
    # --------------------------------------------------------

    messages = []

    if system_context:

        messages.append({
            "role": "system",
            "content": system_context
        })

    messages.append({
        "role": "user",
        "content": f"""
User task:

{task}

The planning agent created the following plan:

{plan}

Execute this plan step-by-step.

Important:

- Follow the plan.
- Use tools when necessary.
- Complete each step before moving
  to the next step.
- Track what has already been completed.
- Do not repeat completed actions.
- If a step fails, analyze the error and
  try to recover when possible.
- At the end, provide a summary of
  completed work.
"""
    })

    # --------------------------------------------------------
    # STEP 3 — EXECUTION LOOP
    # --------------------------------------------------------

    iteration = 0
    max_iterations = 20

    while iteration < max_iterations:

        iteration += 1

        print(
            f"\n--- Execution iteration "
            f"{iteration} ---"
        )

        data = call_ollama(
            messages,
            tools=ALL_TOOLS
        )

        assistant_message = data["message"]

        tool_calls = assistant_message.get(
            "tool_calls",
            []
        )

        # ----------------------------------------------------
        # NO MORE TOOLS
        # ----------------------------------------------------

        if not tool_calls:

            return assistant_message.get(
                "content",
                "Task completed."
            )

        # ----------------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # ----------------------------------------------------

        messages.append(assistant_message)

        # ----------------------------------------------------
        # EXECUTE TOOLS
        # ----------------------------------------------------

        for tool_call in tool_calls:

            fn_name = tool_call["function"]["name"]

            fn_args = tool_call[
                "function"
            ].get(
                "arguments",
                {}
            )

            print(
                f"\nAgent Action:"
                f" {fn_name}({fn_args})"
            )

            fn_to_call = TOOL_MAP.get(fn_name)

            if fn_to_call:

                try:

                    result = fn_to_call(**fn_args)

                except Exception as e:

                    result = (
                        f"Tool execution error: {e}"
                    )

            else:

                result = (
                    f"Error: Tool '{fn_name}' "
                    f"not found."
                )

            print(f"Result: {result}")

            # ------------------------------------------------
            # SEND RESULT BACK TO MODEL
            # ------------------------------------------------

            messages.append({
                "role": "tool",
                "content": result
            })

    return (
        "The agent reached the maximum "
        "number of execution iterations."
    )


# ============================================================
# MAIN
# ============================================================


def main():

    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not OLLAMA_API_KEY:

        print(
            "ERROR: Please set "
            "OLLAMA_API_KEY in your .env file."
        )

        return

    # --------------------------------------------------------
    # START AGENT
    # --------------------------------------------------------

    print(
        f"\nV4 Planning Agent started!"
    )

    print(
        f"Model: {MODEL_NAME}"
    )

    print(
        "\nThis agent can:"
    )

    print("1. Create a plan")
    print("2. Break tasks into steps")
    print("3. Execute tools sequentially")
    print("4. Track execution")
    print("5. Create folders and files")

    print(
        "\nExample:"
    )

    print(
        "Create a project folder named demo, "
        "create README.md inside it, and create "
        "a notes folder containing todo.txt."
    )

    print(
        "\nType 'exit' to quit.\n"
    )

    # --------------------------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------------------------

    system_prompt = """

You are a planning and execution agent.

You have access to these tools:

- list_files
- read_file
- create_folder
- create_file

Your job is to execute multi-step tasks.

The task has already been planned.

Follow the provided plan.

Important rules:

1. Execute tasks sequentially.
2. Use tools whenever required.
3. Do not claim an action was completed
   unless the tool actually succeeded.
4. Keep track of completed actions.
5. Do not unnecessarily repeat actions.
6. If a tool fails, analyze the result.
7. Continue with remaining steps when possible.
8. At the end, clearly summarize what happened.
"""

    # --------------------------------------------------------
    # USER LOOP
    # --------------------------------------------------------

    while True:

        try:

            user_input = input("You: ")

        except KeyboardInterrupt:

            print(
                "\n\nExiting agent..."
            )

            break

        except EOFError:

            print(
                "\n\nExiting agent..."
            )

            break

        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if user_input.lower().strip() in [
            "exit",
            "quit"
        ]:

            print(
                "Shutting down..."
            )

            break

        # ----------------------------------------------------
        # EMPTY INPUT
        # ----------------------------------------------------

        if not user_input.strip():

            continue

        # ----------------------------------------------------
        # RUN AGENT
        # ----------------------------------------------------

        print(
            "\nAgent is planning and "
            "executing your task..."
        )

        try:

            response = run_agent(
                user_input,
                system_context=system_prompt
            )

            print(
                "\nFINAL RESULT:"
            )

            print(response)

        except Exception as e:

            print(
                f"\nERROR: {e}"
            )

        print(
            "\n" + "-" * 60
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()