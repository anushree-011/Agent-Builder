import os
import time
import sqlite3
import requests
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemma4:31b"
)

OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY",
    ""
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)


# ============================================================
# V7 — SAFETY & HUMAN APPROVAL
# ============================================================
#
# V1 → Conversation
# V2 → File reading
# V3 → File creation
# V4 → Planning
# V5 → Reusable tools
# V6 → Memory
# V7 → Safety & Human Approval
#
# V7 introduces:
#
# 1. Tool risk levels
# 2. Safety validation
# 3. Human approval
# 4. Approval before risky actions
# 5. Action descriptions
# 6. Access control
# 7. Error handling
#
# ============================================================


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "agent_memory.db"
)


# ============================================================
# MEMORY DATABASE
# ============================================================


class MemoryDatabase:

    def __init__(
        self,
        database_path
    ):

        self.database_path = database_path

        self.initialize_database()

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    def connect(self):

        return sqlite3.connect(
            self.database_path
        )

    # --------------------------------------------------------
    # INITIALIZE
    # --------------------------------------------------------

    def initialize_database(self):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()

        connection.close()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    def save_memory(
        self,
        memory,
        category="general"
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO memories
            (memory, category)
            VALUES (?, ?)
            """,
            (
                memory,
                category
            )
        )

        connection.commit()

        memory_id = cursor.lastrowid

        connection.close()

        return memory_id

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    def search_memories(
        self,
        keyword
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, memory, category, created_at
            FROM memories
            WHERE memory LIKE ?
            ORDER BY id DESC
            """,
            (
                f"%{keyword}%",
            )
        )

        rows = cursor.fetchall()

        connection.close()

        return rows

    # --------------------------------------------------------
    # ALL
    # --------------------------------------------------------

    def get_all_memories(self):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, memory, category, created_at
            FROM memories
            ORDER BY id ASC
            """
        )

        rows = cursor.fetchall()

        connection.close()

        return rows

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    def delete_memory(
        self,
        memory_id
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM memories
            WHERE id = ?
            """,
            (
                memory_id,
            )
        )

        deleted = cursor.rowcount

        connection.commit()

        connection.close()

        if deleted:

            return (
                f"Memory {memory_id} "
                f"deleted successfully."
            )

        return (
            f"Memory {memory_id} "
            f"not found."
        )


# ============================================================
# CREATE MEMORY DATABASE
# ============================================================

memory_db = MemoryDatabase(
    DATABASE_PATH
)


# ============================================================
# SAFETY LEVELS
# ============================================================

SAFE = "safe"

APPROVAL_REQUIRED = "approval_required"

HIGH_RISK = "high_risk"


# ============================================================
# TOOL REGISTRY
# ============================================================


class ToolRegistry:
    """
    V7 Tool Registry.

    Each tool contains:

    - Python function
    - Ollama schema
    - Risk level
    - Human-readable action description
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
        parameters,
        risk_level=SAFE,
        action_description=""
    ):

        def decorator(function):

            self.tools[name] = {

                "function":
                    function,

                "risk_level":
                    risk_level,

                "action_description":
                    action_description,

                "schema": {

                    "type":
                        "function",

                    "function": {

                        "name":
                            name,

                        "description":
                            description,

                        "parameters":
                            parameters
                    }
                }
            }

            return function

        return decorator

    # --------------------------------------------------------
    # GET SCHEMAS
    # --------------------------------------------------------

    def get_schemas(self):

        return [
            tool["schema"]
            for tool in self.tools.values()
        ]

    # --------------------------------------------------------
    # GET TOOL
    # --------------------------------------------------------

    def get_tool(
        self,
        name
    ):

        return self.tools.get(
            name
        )

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    def execute(
        self,
        name,
        arguments
    ):

        tool = self.get_tool(
            name
        )

        if not tool:

            return (
                f"Error: Tool '{name}' "
                f"is not registered."
            )

        function = tool["function"]

        try:

            return function(
                **arguments
            )

        except Exception as e:

            return (
                f"Error executing "
                f"'{name}': {e}"
            )

    # --------------------------------------------------------
    # LIST
    # --------------------------------------------------------

    def list_tools(self):

        return list(
            self.tools.keys()
        )


# ============================================================
# CREATE REGISTRY
# ============================================================

registry = ToolRegistry()


# ============================================================
# FILE TOOL — LIST FILES
# ============================================================


@registry.register(

    name="list_files",

    description=(
        "Lists files and folders "
        "inside a directory."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "directory": {

                "type":
                    "string",

                "description":
                    "Directory to list."
            }
        }
    },

    risk_level=SAFE,

    action_description=(
        "List files and folders."
    )
)
def list_files(
    directory="."
):

    try:

        items = os.listdir(
            directory
        )

        if not items:

            return (
                f"Directory "
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

            kind = (
                "FOLDER"
                if os.path.isdir(
                    full_path
                )
                else "FILE"
            )

            result += (
                f"  {kind}: {item}\n"
            )

        return result

    except Exception as e:

        return (
            f"Error: {e}"
        )


# ============================================================
# FILE TOOL — READ FILE
# ============================================================


@registry.register(

    name="read_file",

    description=(
        "Reads a text file."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "filepath": {

                "type":
                    "string",

                "description":
                    "Path to file."
            }
        },

        "required": [
            "filepath"
        ]
    },

    risk_level=SAFE,

    action_description=(
        "Read a file."
    )
)
def read_file(
    filepath
):

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        return content[:5000]

    except Exception as e:

        return (
            f"Error reading file: {e}"
        )


# ============================================================
# FILE TOOL — CREATE FOLDER
# ============================================================


@registry.register(

    name="create_folder",

    description=(
        "Creates a folder."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "folder_path": {

                "type":
                    "string",

                "description":
                    "Folder path."
            }
        },

        "required": [
            "folder_path"
        ]
    },

    risk_level=APPROVAL_REQUIRED,

    action_description=(
        "Create a new folder "
        "on the computer."
    )
)
def create_folder(
    folder_path
):

    try:

        os.makedirs(
            folder_path,
            exist_ok=True
        )

        return (
            f"Success: Folder "
            f"'{folder_path}' created."
        )

    except Exception as e:

        return (
            f"Error creating folder: {e}"
        )


# ============================================================
# FILE TOOL — CREATE FILE
# ============================================================


@registry.register(

    name="create_file",

    description=(
        "Creates a file "
        "with specified content."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "filepath": {

                "type":
                    "string",

                "description":
                    "File path."
            },

            "content": {

                "type":
                    "string",

                "description":
                    "Content to write."
            }
        },

        "required": [
            "filepath"
        ]
    },

    risk_level=APPROVAL_REQUIRED,

    action_description=(
        "Create or overwrite a file "
        "on the computer."
    )
)
def create_file(
    filepath,
    content=""
):

    try:

        parent = os.path.dirname(
            filepath
        )

        if (
            parent
            and not os.path.exists(parent)
        ):

            os.makedirs(
                parent,
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
            f"'{filepath}' created."
        )

    except Exception as e:

        return (
            f"Error creating file: {e}"
        )


# ============================================================
# CALCULATOR
# ============================================================


@registry.register(

    name="calculate",

    description=(
        "Performs basic "
        "mathematical calculations."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "number1": {

                "type":
                    "number"
            },

            "number2": {

                "type":
                    "number"
            },

            "operator": {

                "type":
                    "string",

                "description":
                    "+, -, *, or /"
            }
        },

        "required": [
            "number1",
            "number2",
            "operator"
        ]
    },

    risk_level=SAFE,

    action_description=(
        "Perform a calculation."
    )
)
def calculate(
    number1,
    number2,
    operator
):

    if operator == "+":

        return str(
            number1 + number2
        )

    if operator == "-":

        return str(
            number1 - number2
        )

    if operator == "*":

        return str(
            number1 * number2
        )

    if operator == "/":

        if number2 == 0:

            return (
                "Error: Cannot "
                "divide by zero."
            )

        return str(
            number1 / number2
        )

    return (
        "Error: Invalid operator."
    )


# ============================================================
# MEMORY — SAVE
# ============================================================


@registry.register(

    name="save_memory",

    description=(
        "Saves useful information "
        "into long-term memory."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "memory": {

                "type":
                    "string",

                "description":
                    "Information to remember."
            },

            "category": {

                "type":
                    "string",

                "description":
                    "Memory category."
            }
        },

        "required": [
            "memory"
        ]
    },

    risk_level=APPROVAL_REQUIRED,

    action_description=(
        "Save information into "
        "the agent's long-term memory."
    )
)
def save_memory(
    memory,
    category="general"
):

    memory_id = memory_db.save_memory(
        memory,
        category
    )

    return (
        f"Memory saved successfully "
        f"with ID {memory_id}."
    )


# ============================================================
# MEMORY — SEARCH
# ============================================================


@registry.register(

    name="search_memory",

    description=(
        "Searches long-term memory."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "keyword": {

                "type":
                    "string",

                "description":
                    "Keyword to search."
            }
        },

        "required": [
            "keyword"
        ]
    },

    risk_level=SAFE,

    action_description=(
        "Search stored memories."
    )
)
def search_memory(
    keyword
):

    memories = (
        memory_db.search_memories(
            keyword
        )
    )

    if not memories:

        return (
            "No matching memories found."
        )

    result = (
        "Matching memories:\n"
    )

    for (
        memory_id,
        memory,
        category,
        created_at
    ) in memories:

        result += (
            f"[{memory_id}] "
            f"({category}) "
            f"{memory}\n"
        )

    return result


# ============================================================
# MEMORY — DELETE
# ============================================================


@registry.register(

    name="delete_memory",

    description=(
        "Deletes a stored memory."
    ),

    parameters={

        "type":
            "object",

        "properties": {

            "memory_id": {

                "type":
                    "integer",

                "description":
                    "Memory ID."
            }
        },

        "required": [
            "memory_id"
        ]
    },

    risk_level=APPROVAL_REQUIRED,

    action_description=(
        "Delete information from "
        "long-term memory."
    )
)
def delete_memory(
    memory_id
):

    return memory_db.delete_memory(
        memory_id
    )


# ============================================================
# SAFETY SYSTEM
# ============================================================


class SafetyManager:
    """
    Controls whether a tool can execute.
    """

    def __init__(
        self,
        require_approval=True
    ):

        self.require_approval = (
            require_approval
        )

    # --------------------------------------------------------
    # CHECK TOOL
    # --------------------------------------------------------

    def check_tool(
        self,
        tool,
        arguments
    ):

        risk_level = tool[
            "risk_level"
        ]

        # ----------------------------------------------------
        # SAFE ACTION
        # ----------------------------------------------------

        if risk_level == SAFE:

            return True

        # ----------------------------------------------------
        # APPROVAL REQUIRED
        # ----------------------------------------------------

        if (
            risk_level
            == APPROVAL_REQUIRED
        ):

            return self.request_approval(
                tool,
                arguments
            )

        # ----------------------------------------------------
        # HIGH RISK
        # ----------------------------------------------------

        if risk_level == HIGH_RISK:

            return self.request_high_risk_approval(
                tool,
                arguments
            )

        # ----------------------------------------------------
        # UNKNOWN RISK
        # ----------------------------------------------------

        print(
            "\n⚠️ UNKNOWN TOOL RISK"
        )

        print(
            "Action blocked for safety."
        )

        return False

    # --------------------------------------------------------
    # NORMAL APPROVAL
    # --------------------------------------------------------

    def request_approval(
        self,
        tool,
        arguments
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            "⚠️ HUMAN APPROVAL REQUIRED"
        )

        print(
            "=" * 60
        )

        print(
            f"\nAction:"
        )

        print(
            tool["action_description"]
        )

        print(
            f"\nTool:"
        )

        print(
            tool["schema"]
            ["function"]
            ["name"]
        )

        print(
            f"\nArguments:"
        )

        print(
            arguments
        )

        print(
            "\nDo you approve this action?"
        )

        answer = input(
            "Type 'yes' or 'no': "
        )

        return (
            answer.lower().strip()
            in [
                "yes",
                "y"
            ]
        )

    # --------------------------------------------------------
    # HIGH RISK APPROVAL
    # --------------------------------------------------------

    def request_high_risk_approval(
        self,
        tool,
        arguments
    ):

        print(
            "\n" + "!" * 60
        )

        print(
            "🚨 HIGH-RISK ACTION"
        )

        print(
            "!" * 60
        )

        print(
            "\nThis action can significantly "
            "affect the computer."
        )

        print(
            f"\nAction:"
        )

        print(
            tool["action_description"]
        )

        print(
            f"\nArguments:"
        )

        print(
            arguments
        )

        print(
            "\nType exactly:"
        )

        print(
            "APPROVE"
        )

        answer = input(
            "Confirmation: "
        )

        return (
            answer.strip()
            == "APPROVE"
        )


# ============================================================
# CREATE SAFETY MANAGER
# ============================================================

safety_manager = SafetyManager()


# ============================================================
# OLLAMA API
# ============================================================


def call_ollama(
    messages,
    tools=None
):

    payload = {

        "model":
            MODEL_NAME,

        "messages":
            messages,

        "stream":
            False,

        "options": {

            "temperature":
                0.2
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
# SHORT-TERM MEMORY
# ============================================================


conversation_history = []


# ============================================================
# AGENT
# ============================================================


def run_agent(
    user_input
):

    conversation_history.append({

        "role":
            "user",

        "content":
            user_input
    })

    system_message = {

        "role":
            "system",

        "content":
            """
You are V7 Safety Agent.

You have access to tools.

Some tools are safe and some require
human approval.

Never attempt to bypass the safety
system.

Never claim that a tool was executed
unless the tool result confirms it.

If a tool requires approval, the
application will ask the human.

Use tools only when they are necessary.

Respect the user's instructions.
"""
    }

    messages = [
        system_message
    ]

    messages.extend(
        conversation_history[-10:]
    )

    # --------------------------------------------------------
    # AGENT LOOP
    # --------------------------------------------------------

    max_iterations = 20

    for iteration in range(
        max_iterations
    ):

        print(
            f"\n--- Agent iteration "
            f"{iteration + 1} ---"
        )

        data = call_ollama(

            messages,

            tools=registry.get_schemas()
        )

        assistant_message = (
            data["message"]
        )

        tool_calls = (
            assistant_message.get(
                "tool_calls",
                []
            )
        )

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        if not tool_calls:

            response = (
                assistant_message.get(
                    "content",
                    "Task completed."
                )
            )

            conversation_history.append({

                "role":
                    "assistant",

                "content":
                    response
            })

            return response

        # ----------------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # ----------------------------------------------------

        messages.append(
            assistant_message
        )

        # ----------------------------------------------------
        # TOOL EXECUTION
        # ----------------------------------------------------

        for tool_call in tool_calls:

            function_data = (
                tool_call["function"]
            )

            tool_name = (
                function_data["name"]
            )

            arguments = (
                function_data.get(
                    "arguments",
                    {}
                )
            )

            print(
                f"\nTool requested: "
                f"{tool_name}"
            )

            print(
                f"Arguments: "
                f"{arguments}"
            )

            # ------------------------------------------------
            # FIND TOOL
            # ------------------------------------------------

            tool = registry.get_tool(
                tool_name
            )

            if not tool:

                result = (
                    f"Error: Tool "
                    f"'{tool_name}' "
                    f"does not exist."
                )

                print(result)

                messages.append({

                    "role":
                        "tool",

                    "content":
                        result
                })

                continue

            # ------------------------------------------------
            # SAFETY CHECK
            # ------------------------------------------------

            approved = (
                safety_manager.check_tool(
                    tool,
                    arguments
                )
            )

            # ------------------------------------------------
            # BLOCKED
            # ------------------------------------------------

            if not approved:

                result = (
                    "ACTION BLOCKED: "
                    "Human approval was not "
                    "given."
                )

                print(
                    "\n🛑 "
                    + result
                )

            # ------------------------------------------------
            # APPROVED
            # ------------------------------------------------

            else:

                print(
                    "\n✅ Action approved."
                )

                result = (
                    registry.execute(
                        tool_name,
                        arguments
                    )
                )

                print(
                    f"Tool result: "
                    f"{result}"
                )

            # ------------------------------------------------
            # SEND RESULT BACK TO MODEL
            # ------------------------------------------------

            messages.append({

                "role":
                    "tool",

                "content":
                    result
            })

    return (
        "Agent stopped because maximum "
        "iterations were reached."
    )


# ============================================================
# MAIN
# ============================================================


def main():

    if not OLLAMA_API_KEY:

        print(
            "ERROR: Please set "
            "OLLAMA_API_KEY in .env"
        )

        return

    print(
        "\n" + "=" * 60
    )

    print(
        "V7 — SAFETY & HUMAN APPROVAL"
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

    for tool_name in (
        registry.list_tools()
    ):

        tool = registry.get_tool(
            tool_name
        )

        print(
            f"  - {tool_name}"
            f" [{tool['risk_level']}]"
        )

    print(
        "\nSafety system:"
    )

    print(
        "  🟢 SAFE → automatic execution"
    )

    print(
        "  🟡 APPROVAL REQUIRED → ask user"
    )

    print(
        "  🔴 HIGH RISK → explicit approval"
    )

    print(
        "\nExamples:"
    )

    print(
        "  Calculate 25 * 8"
    )

    print(
        "  List files in the current directory"
    )

    print(
        "  Create a file called test.txt"
    )

    print(
        "  Remember that I like Java"
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
            "\nAgent is thinking..."
        )

        try:

            response = run_agent(
                user_input
            )

            print(
                "\nAgent:"
            )

            print(
                response
            )

        except Exception as e:

            print(
                f"\nERROR: {e}"
            )

        print(
            "\n" + "-" * 60
        )


# ============================================================
# ENTRY POINT
# ============================================================


if __name__ == "__main__":

    main()