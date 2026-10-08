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

OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY",
    ""
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)


# ============================================================
# V5 — REUSABLE TOOL SYSTEM
# ============================================================
#
# V1 → Chat agent
# V2 → File reading
# V3 → File creation
# V4 → Planning + execution
# V5 → Reusable Tool Registry
#
# Main idea:
#
# New tools should be addable without changing
# the main agent execution loop.
#
# ============================================================


# ============================================================
# CONCEPT 1: TOOL REGISTRY
# ============================================================


class ToolRegistry:
    """
    Central registry for all tools available to the agent.

    The registry stores:
        1. Python function
        2. Tool schema
        3. Tool description

    The agent does not need to know how individual
    tools are implemented.
    """

    def __init__(self):

        self.tools = {}

    # --------------------------------------------------------
    # REGISTER TOOL
    # --------------------------------------------------------

    def register(
        self,
        name,
        description,
        parameters
    ):
        """
        Decorator used to register a Python function
        as an agent tool.
        """

        def decorator(function):

            self.tools[name] = {
                "function": function,

                "schema": {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters
                    }
                }
            }

            return function

        return decorator

    # --------------------------------------------------------
    # GET TOOL SCHEMAS
    # --------------------------------------------------------

    def get_schemas(self):

        return [
            tool["schema"]
            for tool in self.tools.values()
        ]

    # --------------------------------------------------------
    # EXECUTE TOOL
    # --------------------------------------------------------

    def execute(
        self,
        name,
        arguments
    ):
        """
        Execute a registered tool by name.
        """

        if name not in self.tools:

            return (
                f"Error: Tool '{name}' "
                f"is not registered."
            )

        function = self.tools[name]["function"]

        try:

            return function(**arguments)

        except Exception as e:

            return (
                f"Error executing tool "
                f"'{name}': {e}"
            )

    # --------------------------------------------------------
    # LIST TOOLS
    # --------------------------------------------------------

    def list_tools(self):

        return list(self.tools.keys())


# ============================================================
# CREATE GLOBAL TOOL REGISTRY
# ============================================================

registry = ToolRegistry()


# ============================================================
# CONCEPT 2: FILE TOOLS
# ============================================================


@registry.register(
    name="list_files",

    description=(
        "Lists all files and folders "
        "inside a directory."
    ),

    parameters={
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
)
def list_files(directory="."):
    """
    Lists files and folders inside a directory.
    """

    try:

        items = os.listdir(directory)

        if not items:

            return (
                f"The directory "
                f"'{directory}' is empty."
            )

        result = (
            f"Contents of "
            f"'{directory}':\n"
        )

        for item in items:

            full_path = os.path.join(
                directory,
                item
            )

            if os.path.isdir(full_path):

                kind = "FOLDER"

            else:

                kind = "FILE"

            result += (
                f"  {kind}: {item}\n"
            )

        return result

    except FileNotFoundError:

        return (
            f"Error: Directory "
            f"'{directory}' not found."
        )

    except PermissionError:

        return (
            f"Error: Permission denied "
            f"for '{directory}'."
        )

    except Exception as e:

        return (
            f"Error listing directory: {e}"
        )


# ============================================================
# READ FILE
# ============================================================


@registry.register(
    name="read_file",

    description=(
        "Reads text content from "
        "an existing file."
    ),

    parameters={
        "type": "object",

        "properties": {

            "filepath": {
                "type": "string",
                "description": (
                    "Path to the file."
                )
            }

        },

        "required": [
            "filepath"
        ]
    }
)
def read_file(filepath):
    """
    Reads a text file.
    """

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        if len(content) > 3000:

            return (
                content[:3000]
                + "\n\n"
                + "[...File truncated...]"
            )

        return content

    except FileNotFoundError:

        return (
            f"Error: File "
            f"'{filepath}' not found."
        )

    except Exception as e:

        return (
            f"Error reading file: {e}"
        )


# ============================================================
# CREATE FOLDER
# ============================================================


@registry.register(
    name="create_folder",

    description=(
        "Creates a folder and any "
        "required parent folders."
    ),

    parameters={
        "type": "object",

        "properties": {

            "folder_path": {
                "type": "string",
                "description": (
                    "Path of the folder "
                    "to create."
                )
            }

        },

        "required": [
            "folder_path"
        ]
    }
)
def create_folder(folder_path):
    """
    Creates a folder.
    """

    try:

        os.makedirs(
            folder_path,
            exist_ok=True
        )

        return (
            f"Success: Folder "
            f"'{folder_path}' "
            f"created successfully."
        )

    except Exception as e:

        return (
            f"Error creating folder "
            f"'{folder_path}': {e}"
        )


# ============================================================
# CREATE FILE
# ============================================================


@registry.register(
    name="create_file",

    description=(
        "Creates a file with "
        "specified text content."
    ),

    parameters={
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
                    "Text content to "
                    "write inside file."
                )
            }

        },

        "required": [
            "filepath"
        ]
    }
)
def create_file(
    filepath,
    content=""
):
    """
    Creates a file.
    """

    try:

        parent_dir = os.path.dirname(
            filepath
        )

        if (
            parent_dir
            and not os.path.exists(parent_dir)
        ):

            os.makedirs(
                parent_dir,
                exist_ok=True
            )

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

        return (
            f"Success: File "
            f"'{filepath}' "
            f"created successfully "
            f"({len(content)} characters)."
        )

    except Exception as e:

        return (
            f"Error creating file "
            f"'{filepath}': {e}"
        )


# ============================================================
# V5 DEMONSTRATION TOOL
# ============================================================
#
# This tool demonstrates how easy it is to add a
# completely new capability.
#
# Notice:
#
# We DO NOT modify:
#
# - run_agent()
# - call_ollama()
# - ToolRegistry
#
# We only define and register the new tool.
# ============================================================


@registry.register(
    name="calculate",

    description=(
        "Performs a basic mathematical "
        "calculation using two numbers "
        "and an operator."
    ),

    parameters={
        "type": "object",

        "properties": {

            "number1": {
                "type": "number",
                "description": "First number."
            },

            "number2": {
                "type": "number",
                "description": "Second number."
            },

            "operator": {
                "type": "string",
                "description": (
                    "Operator: +, -, *, or /"
                )
            }

        },

        "required": [
            "number1",
            "number2",
            "operator"
        ]
    }
)
def calculate(
    number1,
    number2,
    operator
):
    """
    Performs basic arithmetic.
    """

    try:

        if operator == "+":

            result = number1 + number2

        elif operator == "-":

            result = number1 - number2

        elif operator == "*":

            result = number1 * number2

        elif operator == "/":

            if number2 == 0:

                return (
                    "Error: Cannot divide by zero."
                )

            result = number1 / number2

        else:

            return (
                "Error: Unsupported operator. "
                "Use +, -, *, or /."
            )

        return (
            f"Result: {number1} "
            f"{operator} {number2} = {result}"
        )

    except Exception as e:

        return (
            f"Calculation error: {e}"
        )


# ============================================================
# CONCEPT 3: OLLAMA API
# ============================================================


def call_ollama(
    messages,
    tools=None
):
    """
    Sends a chat request to Ollama Cloud.
    """

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

        "Authorization":
            f"Bearer {OLLAMA_API_KEY}",

        "Content-Type":
            "application/json"
    }

    max_retries = 3

    for attempt in range(
        max_retries + 1
    ):

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

                wait = 2 ** (
                    attempt + 1
                )

                print(
                    f"Model busy. "
                    f"Retrying in {wait}s..."
                )

                time.sleep(wait)

            else:

                raise


# ============================================================
# CONCEPT 4: AGENT LOOP
# ============================================================


def run_agent(task):
    """
    Main reusable agent loop.

    Notice that this function does NOT know
    the implementation details of individual
    tools.

    It only communicates with the registry.
    """

    messages = [

        {
            "role": "system",

            "content": """
You are a reusable tool-based AI agent.

You have access to a registry of tools.

Choose the appropriate tool when the
user's task requires an action.

Important rules:

1. Select the correct tool.
2. Provide correct arguments.
3. Do not claim an action succeeded
   unless the tool result confirms it.
4. You may use multiple tools.
5. You may call tools sequentially.
6. After completing the task, explain
   what you did clearly.
"""
        },

        {
            "role": "user",
            "content": task
        }

    ]

    max_iterations = 20

    for iteration in range(
        max_iterations
    ):

        print(
            f"\n--- Agent iteration "
            f"{iteration + 1} ---"
        )

        # ----------------------------------------------------
        # GET RESPONSE
        # ----------------------------------------------------

        data = call_ollama(

            messages,

            tools=registry.get_schemas()
        )

        assistant_message = data["message"]

        tool_calls = assistant_message.get(
            "tool_calls",
            []
        )

        # ----------------------------------------------------
        # NO TOOL CALL
        # ----------------------------------------------------

        if not tool_calls:

            return assistant_message.get(
                "content",
                "Task completed."
            )

        # ----------------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # ----------------------------------------------------

        messages.append(
            assistant_message
        )

        # ----------------------------------------------------
        # EXECUTE TOOLS THROUGH REGISTRY
        # ----------------------------------------------------

        for tool_call in tool_calls:

            function_data = tool_call[
                "function"
            ]

            tool_name = function_data[
                "name"
            ]

            arguments = function_data.get(
                "arguments",
                {}
            )

            print(
                f"\nTool selected: "
                f"{tool_name}"
            )

            print(
                f"Arguments: {arguments}"
            )

            # ------------------------------------------------
            # REGISTRY HANDLES EXECUTION
            # ------------------------------------------------

            result = registry.execute(
                tool_name,
                arguments
            )

            print(
                f"Tool result: {result}"
            )

            # ------------------------------------------------
            # SEND RESULT BACK TO MODEL
            # ------------------------------------------------

            messages.append({

                "role": "tool",

                "content": result

            })

    return (
        "Agent stopped because the "
        "maximum number of iterations "
        "was reached."
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
    # SHOW AVAILABLE TOOLS
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "V5 — REUSABLE TOOL SYSTEM"
    )

    print(
        "=" * 60
    )

    print(
        f"\nModel: {MODEL_NAME}"
    )

    print(
        "\nRegistered tools:"
    )

    for tool_name in registry.list_tools():

        print(
            f"  - {tool_name}"
        )

    print(
        "\nThe agent can dynamically select "
        "tools from the registry."
    )

    print(
        "\nExample tasks:"
    )

    print(
        "1. Create a folder called V5Test."
    )

    print(
        "2. Create a file called hello.txt "
        "with Hello World."
    )

    print(
        "3. Calculate 25 * 8."
    )

    print(
        "4. Create a folder and file, "
        "then calculate 100 / 4."
    )

    print(
        "\nType 'exit' to quit.\n"
    )

    # --------------------------------------------------------
    # USER LOOP
    # --------------------------------------------------------

    while True:

        try:

            user_input = input(
                "You: "
            )

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
            "\nAgent is working..."
        )

        try:

            response = run_agent(
                user_input
            )

            print(
                "\nAgent:"
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