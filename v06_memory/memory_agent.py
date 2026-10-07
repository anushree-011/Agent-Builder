import os
import json
import time
import sqlite3
import requests
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# MODEL AND API CONFIGURATION
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
# V6 — MEMORY AGENT
# ============================================================
#
# V1 → Conversation
# V2 → File reading
# V3 → File creation
# V4 → Planning
# V5 → Reusable tool registry
# V6 → Memory
#
# V6 introduces:
#
# 1. Short-term memory
# 2. Long-term memory
# 3. SQLite persistence
# 4. Memory retrieval
# 5. Memory storage
# 6. Memory deletion
# 7. Conversation state
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
# CONCEPT 1: MEMORY DATABASE
# ============================================================


class MemoryDatabase:
    """
    Handles persistent long-term memory using SQLite.
    """

    def __init__(self, database_path):

        self.database_path = database_path

        self.initialize_database()

    # --------------------------------------------------------
    # DATABASE CONNECTION
    # --------------------------------------------------------

    def connect(self):

        return sqlite3.connect(
            self.database_path
        )

    # --------------------------------------------------------
    # INITIALIZE DATABASE
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()

        connection.close()

    # --------------------------------------------------------
    # SAVE MEMORY
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
    # GET ALL MEMORIES
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
    # SEARCH MEMORY
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
    # DELETE MEMORY
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
# CONCEPT 2: TOOL REGISTRY
# ============================================================


class ToolRegistry:
    """
    Reusable tool registry from V5.

    V6 keeps the same architecture and adds
    memory-related tools.
    """

    def __init__(self):

        self.tools = {}

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    def register(
        self,
        name,
        description,
        parameters
    ):

        def decorator(function):

            self.tools[name] = {

                "function": function,

                "schema": {

                    "type": "function",

                    "function": {

                        "name": name,

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
    # EXECUTE
    # --------------------------------------------------------

    def execute(
        self,
        name,
        arguments
    ):

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
                f"Error executing "
                f"'{name}': {e}"
            )

    # --------------------------------------------------------
    # LIST TOOLS
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
# FILE TOOL 1 — LIST FILES
# ============================================================


@registry.register(

    name="list_files",

    description=(
        "Lists files and folders "
        "inside a directory."
    ),

    parameters={

        "type": "object",

        "properties": {

            "directory": {

                "type": "string",

                "description":
                    "Directory path."
            }
        }
    }
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
                if os.path.isdir(full_path)
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
# FILE TOOL 2 — READ FILE
# ============================================================


@registry.register(

    name="read_file",

    description=(
        "Reads the contents "
        "of a text file."
    ),

    parameters={

        "type": "object",

        "properties": {

            "filepath": {

                "type": "string",

                "description":
                    "Path to file."
            }
        },

        "required": [
            "filepath"
        ]
    }
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
# FILE TOOL 3 — CREATE FOLDER
# ============================================================


@registry.register(

    name="create_folder",

    description=(
        "Creates a folder."
    ),

    parameters={

        "type": "object",

        "properties": {

            "folder_path": {

                "type": "string",

                "description":
                    "Folder path."
            }
        },

        "required": [
            "folder_path"
        ]
    }
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
            f"Error: {e}"
        )


# ============================================================
# FILE TOOL 4 — CREATE FILE
# ============================================================


@registry.register(

    name="create_file",

    description=(
        "Creates a file "
        "with specified content."
    ),

    parameters={

        "type": "object",

        "properties": {

            "filepath": {

                "type": "string",

                "description":
                    "File path."
            },

            "content": {

                "type": "string",

                "description":
                    "File content."
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
            f"Error: {e}"
        )


# ============================================================
# TOOL 5 — CALCULATE
# ============================================================


@registry.register(

    name="calculate",

    description=(
        "Performs basic "
        "mathematical calculations."
    ),

    parameters={

        "type": "object",

        "properties": {

            "number1": {

                "type": "number"
            },

            "number2": {

                "type": "number"
            },

            "operator": {

                "type": "string",

                "description":
                    "+, -, *, or /"
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

    if operator == "+":

        return str(
            number1 + number2
        )

    elif operator == "-":

        return str(
            number1 - number2
        )

    elif operator == "*":

        return str(
            number1 * number2
        )

    elif operator == "/":

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
# MEMORY TOOL 1 — SAVE MEMORY
# ============================================================


@registry.register(

    name="save_memory",

    description=(
        "Saves useful information "
        "about the user or previous "
        "tasks into long-term memory."
    ),

    parameters={

        "type": "object",

        "properties": {

            "memory": {

                "type": "string",

                "description":
                    "Information to remember."
            },

            "category": {

                "type": "string",

                "description":
                    "Memory category such as "
                    "preference, project, "
                    "fact, or task."
            }
        },

        "required": [
            "memory"
        ]
    }
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
# MEMORY TOOL 2 — SEARCH MEMORY
# ============================================================


@registry.register(

    name="search_memory",

    description=(
        "Searches long-term memory "
        "for previously stored information."
    ),

    parameters={

        "type": "object",

        "properties": {

            "keyword": {

                "type": "string",

                "description":
                    "Keyword to search for."
            }
        },

        "required": [
            "keyword"
        ]
    }
)
def search_memory(
    keyword
):

    memories = memory_db.search_memories(
        keyword
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
# MEMORY TOOL 3 — SHOW ALL MEMORY
# ============================================================


@registry.register(

    name="show_memories",

    description=(
        "Shows all long-term memories "
        "stored by the agent."
    ),

    parameters={

        "type": "object",

        "properties": {}
    }
)
def show_memories():

    memories = (
        memory_db.get_all_memories()
    )

    if not memories:

        return (
            "No memories stored."
        )

    result = (
        "Stored memories:\n"
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
# MEMORY TOOL 4 — DELETE MEMORY
# ============================================================


@registry.register(

    name="delete_memory",

    description=(
        "Deletes a stored memory "
        "using its memory ID."
    ),

    parameters={

        "type": "object",

        "properties": {

            "memory_id": {

                "type": "integer",

                "description":
                    "ID of memory to delete."
            }
        },

        "required": [
            "memory_id"
        ]
    }
)
def delete_memory(
    memory_id
):

    return memory_db.delete_memory(
        memory_id
    )


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
# AUTOMATIC MEMORY RETRIEVAL
# ============================================================


def get_relevant_memories(
    user_input
):
    """
    Simple keyword-based memory retrieval.

    V6 intentionally uses a simple approach.
    Semantic/vector memory can be added later.
    """

    words = user_input.lower().split()

    useful_memories = []

    for word in words:

        if len(word) < 4:

            continue

        memories = (
            memory_db.search_memories(
                word
            )
        )

        for memory in memories:

            if memory not in useful_memories:

                useful_memories.append(
                    memory
                )

    return useful_memories[:5]


# ============================================================
# AGENT
# ============================================================


def run_agent(
    user_input
):

    # --------------------------------------------------------
    # RETRIEVE RELEVANT LONG-TERM MEMORY
    # --------------------------------------------------------

    relevant_memories = (
        get_relevant_memories(
            user_input
        )
    )

    memory_context = ""

    if relevant_memories:

        memory_context = (
            "\n\nRelevant memories:\n"
        )

        for (
            memory_id,
            memory,
            category,
            created_at
        ) in relevant_memories:

            memory_context += (
                f"- {memory}\n"
            )

    # --------------------------------------------------------
    # ADD USER MESSAGE TO SHORT-TERM MEMORY
    # --------------------------------------------------------

    conversation_history.append({

        "role":
            "user",

        "content":
            user_input
    })

    # --------------------------------------------------------
    # BUILD SYSTEM MESSAGE
    # --------------------------------------------------------

    system_message = {

        "role":
            "system",

        "content":
            f"""
You are V6 Memory Agent.

You have short-term memory containing
the current conversation.

You also have long-term memory stored
in SQLite.

Use the memory tools when appropriate.

Important rules:

1. Remember useful user preferences,
   project information, and important
   facts when appropriate.

2. Use search_memory when previous
   information may help answer the user.

3. Use save_memory when the user
   explicitly asks you to remember
   something or when information is
   clearly useful for future tasks.

4. Do not invent memories.

5. Do not claim to remember something
   unless it exists in memory.

6. Use delete_memory when the user
   asks to forget a stored memory.

7. Continue using the reusable
   ToolRegistry architecture.

{memory_context}
"""
    }

    messages = [
        system_message
    ]

    # --------------------------------------------------------
    # ADD SHORT-TERM MEMORY
    # --------------------------------------------------------

    messages.extend(
        conversation_history[
            -10:
        ]
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
        # EXECUTE TOOLS
        # --------------------------------------------------------

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
                f"\nTool selected: "
                f"{tool_name}"
            )

            print(
                f"Arguments: {arguments}"
            )

            # ------------------------------------------------
            # EXECUTE THROUGH REGISTRY
            # ------------------------------------------------

            result = registry.execute(
                tool_name,
                arguments
            )

            print(
                f"Tool result: {result}"
            )

            # ------------------------------------------------
            # SEND RESULT BACK
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
        "V6 — MEMORY AGENT"
    )

    print(
        "=" * 60
    )

    print(
        f"\nModel: {MODEL_NAME}"
    )

    print(
        f"Memory database:"
    )

    print(
        DATABASE_PATH
    )

    print(
        "\nRegistered tools:"
    )

    for tool_name in (
        registry.list_tools()
    ):

        print(
            f"  - {tool_name}"
        )

    print(
        "\nMemory capabilities:"
    )

    print(
        "  - Short-term conversation memory"
    )

    print(
        "  - Long-term SQLite memory"
    )

    print(
        "  - Save memory"
    )

    print(
        "  - Search memory"
    )

    print(
        "  - Delete memory"
    )

    print(
        "\nType 'exit' to quit."
    )

    print(
        "Type 'show memories' to inspect memory.\n"
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
        # SPECIAL MEMORY COMMAND
        # ----------------------------------------------------

        if user_input.lower().strip() == (
            "show memories"
        ):

            result = show_memories()

            print(
                f"\n{result}"
            )

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
# PROGRAM ENTRY POINT
# ============================================================


if __name__ == "__main__":

    main()