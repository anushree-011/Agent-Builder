import os
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model and API Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:31b")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api")

# =====================================================================
# V3 — FILE CREATION AGENT
# =====================================================================
# In V1, the agent could only talk.
# In V2, the agent could read files (read-only access).
# In V3, we give the agent ACTIONS that produce STATE CHANGES —
# specifically, creating folders and writing new files!
#
# KEY CONCEPTS IN THIS FILE:
# 1. State-Changing Tools — functions that mutate the local filesystem
# 2. Path Handling & Safety — ensuring directories exist before file creation
# 3. Tool Schemas — telling Ollama about file & folder creation capabilities
# 4. Agentic Action Loop — executing user creation requests end-to-end
# =====================================================================


# ---------------------------------------------------------
# CONCEPT 1: STATE-CHANGING TOOLS
# ---------------------------------------------------------
# Unlike read-only tools, these tools modify the state of your computer.
# Good practice: Always handle errors gracefully (e.g. invalid paths, permission issues).

def list_files(directory: str = ".") -> str:
    """Lists all files and folders inside a given directory."""
    try:
        items = os.listdir(directory)
        if not items:
            return f"The directory '{directory}' is empty."
        result = f"Contents of '{directory}':\n"
        for item in items:
            full_path = os.path.join(directory, item)
            kind = "📁 FOLDER" if os.path.isdir(full_path) else "📄 FILE"
            result += f"  {kind}: {item}\n"
        return result
    except FileNotFoundError:
        return f"Error: Directory '{directory}' not found."
    except PermissionError:
        return f"Error: Permission denied to read '{directory}'."


def read_file(filepath: str) -> str:
    """Reads and returns the text content of a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 3000:
            return content[:3000] + "\n\n[...File truncated for length...]"
        return content
    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."
    except Exception as e:
        return f"Error reading file: {e}"


def create_folder(folder_path: str) -> str:
    """Creates a new folder at the specified path (including parent directories)."""
    try:
        # os.makedirs creates parent folders automatically if they don't exist
        os.makedirs(folder_path, exist_ok=True)
        return f"Success: Folder '{folder_path}' created successfully."
    except Exception as e:
        return f"Error creating folder '{folder_path}': {e}"


def create_file(filepath: str, content: str = "") -> str:
    """Creates a new file with the specified content."""
    try:
        # Ensure parent directory exists before creating the file
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        # Write content to the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return f"Success: File '{filepath}' created successfully ({len(content)} characters written)."
    except Exception as e:
        return f"Error creating file '{filepath}': {e}"


# ---------------------------------------------------------
# CONCEPT 2: TOOL SCHEMAS FOR OLLAMA
# ---------------------------------------------------------
# We register all 4 tools (read & write capabilities) so Ollama knows how to call them.

ALL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all files and folders inside a given directory path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list. Defaults to current directory '.'."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads text content from an existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Creates a new folder directory (and any necessary parent folders).",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path of the folder to create."}
                },
                "required": ["folder_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates a new text file at the given path with specified text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Target file path to create."},
                    "content": {"type": "string", "description": "Text content to write inside the file."}
                },
                "required": ["filepath"]
            }
        }
    }
]

# Map tool names to actual Python functions
TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
    "create_folder": create_folder,
    "create_file": create_file,
}


# ---------------------------------------------------------
# CONCEPT 3: CALLING OLLAMA WITH RETRY LOGIC
# ---------------------------------------------------------

def call_ollama(messages, tools=None):
    """Sends a chat request to Ollama Cloud API with exponential backoff retries."""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2}
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
            if attempt < max_retries and ("503" in str(e) or "504" in str(e) or "timeout" in str(e).lower()):
                wait = 2 ** (attempt + 1)
                print(f"  ⏳ Model busy, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------
# CONCEPT 4: AGENTIC ACTION LOOP
# ---------------------------------------------------------

def run_agent(task: str, system_context: str) -> str:
    """Runs a full agentic execution loop for tasks involving file & folder creation."""
    messages = []
    if system_context:
        messages.append({"role": "system", "content": system_context})
    messages.append({"role": "user", "content": task})

    while True:
        data = call_ollama(messages, tools=ALL_TOOLS)
        assistant_message = data["message"]
        tool_calls = assistant_message.get("tool_calls", [])

        # If no tool calls requested, the model has completed the response
        if not tool_calls:
            return assistant_message.get("content", "")

        # Save model's tool intent to conversation history
        messages.append(assistant_message)

        # Execute requested tools
        for tool_call in tool_calls:
            fn_name = tool_call["function"]["name"]
            fn_args = tool_call["function"].get("arguments", {})

            print(f"  ⚡ Agent Action: Executing {fn_name}({fn_args})")

            fn_to_call = TOOL_MAP.get(fn_name)
            if fn_to_call:
                result = fn_to_call(**fn_args)
            else:
                result = f"Error: Tool '{fn_name}' not found."

            # Feed tool execution result back into conversation
            messages.append({
                "role": "tool",
                "content": result
            })


def main():
    if not OLLAMA_API_KEY:
        print("❌ ERROR: Please set OLLAMA_API_KEY in your .env file.")
        return

    print(f"🤖 Starting V3 File Creation Agent (Model: {MODEL_NAME} via Ollama Cloud)")
    print("Try asking: 'Create a folder named notes and inside it create summary.txt with content Hello World'")
    print("Type 'exit' to quit.\n")

    system_prompt = (
        "You are an active file creation agent. "
        "You have tools to list files, read files, create folders, and create files on the user's computer. "
        "When asked to create files or folders, use the appropriate tools directly."
    )

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
        if not user_input.strip():
            continue

        print("Agent is thinking & performing actions...")
        try:
            response = run_agent(user_input, system_context=system_prompt)
            print(f"\nAgent: {response}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
        print("-" * 40)


if __name__ == "__main__":
    main()
