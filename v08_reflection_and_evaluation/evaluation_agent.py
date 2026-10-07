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
# V8 — REFLECTION & EVALUATION AGENT
# ============================================================
#
# V1 → Conversation
# V2 → File reading
# V3 → File creation
# V4 → Planning
# V5 → Reusable tools
# V6 → Memory
# V7 → Safety & Human Approval
# V8 → Reflection & Evaluation
#
# V8 introduces:
#
# 1. Result validation
# 2. Reflection
# 3. Evaluation
# 4. Retry logic
# 5. Failure handling
# 6. Iterative workflows
#
# ============================================================


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "agent_memory.db"
)


class MemoryDatabase:

    def __init__(
        self,
        database_path
    ):

        self.database_path = database_path

        self.initialize_database()

    def connect(self):

        return sqlite3.connect(
            self.database_path
        )

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
    Reusable registry for all agent tools.
    """

    def __init__(self):

        self.tools = {}

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

    def get_schemas(self):

        return [
            tool["schema"]
            for tool in self.tools.values()
        ]

    def get_tool(
        self,
        name
    ):

        return self.tools.get(
            name
        )

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

        try:

            return tool["function"](
                **arguments
            )

        except Exception as e:

            return (
                f"Error executing "
                f"'{name}': {e}"
            )

    def list_tools(self):

        return list(
            self.tools.keys()
        )


registry = ToolRegistry()


# ============================================================
# TOOL 1 — LIST FILES
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
# TOOL 2 — READ FILE
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
# TOOL 3 — CREATE FOLDER
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
# TOOL 4 — CREATE FILE
# ============================================================


@registry.register(

    name="create_file",

    description=(
        "Creates a file with "
        "specified content."
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
# TOOL 5 — CALCULATE
# ============================================================


@registry.register(

    name="calculate",

    description=(
        "Performs basic mathematical "
        "calculations."
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
# TOOL 6 — SAVE MEMORY
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
        "long-term memory."
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
# TOOL 7 — SEARCH MEMORY
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
# SAFETY MANAGER
# ============================================================


class SafetyManager:

    def check_tool(
        self,
        tool,
        arguments
    ):

        risk_level = tool[
            "risk_level"
        ]

        if risk_level == SAFE:

            return True

        if (
            risk_level
            == APPROVAL_REQUIRED
        ):

            return self.request_approval(
                tool,
                arguments
            )

        if risk_level == HIGH_RISK:

            return self.request_high_risk_approval(
                tool,
                arguments
            )

        return False

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
            f"\nArguments:"
        )

        print(
            arguments
        )

        answer = input(
            "\nApprove? (yes/no): "
        )

        return (
            answer.lower().strip()
            in ["yes", "y"]
        )

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
            tool["action_description"]
        )

        print(
            f"\nArguments:"
        )

        print(
            arguments
        )

        answer = input(
            "\nType APPROVE to continue: "
        )

        return (
            answer.strip()
            == "APPROVE"
        )


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
# REFLECTION SYSTEM
# ============================================================


def reflect_on_result(
    task,
    tool_name,
    arguments,
    result
):
    """
    Ask the model to evaluate whether
    a tool result successfully completed
    the requested task.
    """

    reflection_messages = [

        {
            "role":
                "system",

            "content":
                """
You are an evaluation agent.

Your job is to check whether an action
actually succeeded.

Evaluate the result carefully.

Return ONLY one of these formats:

PASS
The action successfully achieved
the requested result.

FAIL
The action did not successfully
achieve the requested result.

Do not return anything else.
"""
        },

        {
            "role":
                "user",

            "content":
                f"""
Original task:
{task}

Tool used:
{tool_name}

Arguments:
{arguments}

Tool result:
{result}

Did the action succeed?
"""
        }

    ]

    try:

        data = call_ollama(
            reflection_messages
        )

        evaluation = (
            data["message"]
            .get(
                "content",
                ""
            )
            .strip()
            .upper()
        )

        if evaluation.startswith(
            "PASS"
        ):

            return "PASS"

        if evaluation.startswith(
            "FAIL"
        ):

            return "FAIL"

        # Unknown evaluation
        # should be treated as failure

        return "FAIL"

    except Exception as e:

        print(
            f"Reflection error: {e}"
        )

        return "FAIL"


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
You are V8 Reflection Agent.

You can use tools to complete tasks.

After an action is performed, the
application may evaluate the result.

Important rules:

1. Do not claim success without
   evidence from the tool result.

2. If a result indicates failure,
   attempt a better approach.

3. Do not repeat the exact same
   failed action unnecessarily.

4. Use tools when necessary.

5. Clearly explain the final result.
"""
    }

    messages = [
        system_message
    ]

    messages.extend(
        conversation_history[-10:]
    )

    max_iterations = 15

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
        # TOOL CALLS
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
            # GET TOOL
            # ------------------------------------------------

            tool = registry.get_tool(
                tool_name
            )

            if not tool:

                result = (
                    f"Error: Tool "
                    f"'{tool_name}' "
                    f"not found."
                )

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

            if not approved:

                result = (
                    "ACTION BLOCKED: "
                    "Human approval was "
                    "not provided."
                )

                print(
                    "\n🛑 "
                    + result
                )

                messages.append({

                    "role":
                        "tool",

                    "content":
                        result
                })

                continue

            # ------------------------------------------------
            # EXECUTE
            # ------------------------------------------------

            print(
                "\n✅ Executing tool..."
            )

            result = registry.execute(
                tool_name,
                arguments
            )

            print(
                f"Tool result: "
                f"{result}"
            )

            # ------------------------------------------------
            # REFLECTION
            # ------------------------------------------------

            print(
                "\n🔍 Reflecting..."
            )

            evaluation = (
                reflect_on_result(

                    task=user_input,

                    tool_name=tool_name,

                    arguments=arguments,

                    result=result
                )
            )

            print(
                f"Evaluation: "
                f"{evaluation}"
            )

            # ------------------------------------------------
            # PASS
            # ------------------------------------------------

            if evaluation == "PASS":

                print(
                    "✅ Reflection passed."
                )

                messages.append({

                    "role":
                        "tool",

                    "content":
                        f"""
Tool result:
{result}

Reflection:
PASS

The action was successfully
completed and verified.
"""
                })

            # ------------------------------------------------
            # FAIL
            # ------------------------------------------------

            else:

                print(
                    "❌ Reflection failed."
                )

                print(
                    "The agent will "
                    "attempt recovery."
                )

                messages.append({

                    "role":
                        "tool",

                    "content":
                        f"""
Tool result:
{result}

Reflection:
FAIL

The result was not verified
as successful.

You should analyze the failure
and try a different approach
if possible.
"""
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
        "V8 — REFLECTION & EVALUATION AGENT"
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
        "\nV8 capabilities:"
    )

    print(
        "  ✓ Tool execution"
    )

    print(
        "  ✓ Human approval"
    )

    print(
        "  ✓ Result reflection"
    )

    print(
        "  ✓ Result evaluation"
    )

    print(
        "  ✓ Failure detection"
    )

    print(
        "  ✓ Retry / recovery"
    )

    print(
        "\nExample:"
    )

    print(
        "Create a file called "
        "reflection_test.txt containing "
        "'V8 works'."
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

        if user_input.lower().strip() in [
            "exit",
            "quit"
        ]:

            print(
                "Shutting down..."
            )

            break

        if not user_input.strip():

            continue

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
