import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:31b")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api")

# =====================================================================
# V2 — FILE READING AGENT
# =====================================================================
# In V1 the agent could only talk. It had no access to the real world.
# In V2 we give the agent its first TOOLS — the ability to list and
# read files on your computer. This is a critical agentic concept.
#
# KEY CONCEPTS IN THIS FILE:
# 1. Tools          — functions the AI can decide to call
# 2. Tool Schemas   — how we describe tools to the AI in its language
# 3. Tool Calling   — the back-and-forth cycle between agent & tools
# 4. Agentic Loop   — now handles both text replies AND tool calls
# =====================================================================


# ---------------------------------------------------------
# CONCEPT 1: TOOLS
# ---------------------------------------------------------
# A "tool" is just a regular Python function.
# The agent does NOT run it directly — it *requests* us to run it,
# and we pass the result back. The agent never touches your filesystem
# directly; it can only call these specific, controlled functions.

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
        # Limit output so we don't flood the context window
        if len(content) > 3000:
            return content[:3000] + "\n\n[...File truncated for length...]"
        return content
    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."
    except PermissionError:
        return f"Error: Permission denied to read '{filepath}'."
    except Exception as e:
        return f"Error reading file: {e}"


# ---------------------------------------------------------
# CONCEPT 2: TOOL SCHEMAS
# ---------------------------------------------------------
# The Ollama API needs tool definitions in a specific format.
# We describe each tool so the AI understands:
#   - WHAT each tool is called
#   - WHAT it does (the description)
#   - WHAT parameters to send (and their types)

ALL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all files and folders inside a given directory path on the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The path of the directory to list. Defaults to the current directory '.'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads and returns the full text content of a file from the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The full or relative path to the file to be read."
                    }
                },
                "required": ["filepath"]
            }
        }
    }
]

# A lookup map so we can find and call the right Python function
# when the AI requests a specific tool by name
TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
}


def call_ollama(messages, tools=None):
    """Makes a single API call to Ollama Cloud with retry logic."""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2  # Low temperature = more focused, less creative
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
            if attempt < max_retries and ("503" in str(e) or "504" in str(e) or "timeout" in str(e).lower()):
                wait = 2 ** (attempt + 1)
                print(f"  ⏳ Model busy, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------
# CONCEPT 3: TOOL CALLING (The Agentic Loop)
# ---------------------------------------------------------
# In V1 the loop was simple: send prompt → get text back → done.
# In V2, the AI can respond with a TOOL CALL instead of text.
# When it does, we must:
#   1. Detect that it wants to use a tool
#   2. Run the real Python function ourselves
#   3. Send the result BACK to the AI
#   4. Let the AI generate the final human-readable answer
#
# This back-and-forth is the heart of tool calling.

def run_agent(task: str, system_context: str) -> str:
    """
    Runs one full agentic task cycle, handling any tool calls the model makes.
    """
    # Start the conversation with system prompt + user task
    messages = []
    if system_context:
        messages.append({"role": "system", "content": system_context})
    messages.append({"role": "user", "content": task})

    # The agent loop — keeps going until the model gives a text reply
    while True:
        data = call_ollama(messages, tools=ALL_TOOLS)
        assistant_message = data["message"]

        # Check if the model wants to call tools
        tool_calls = assistant_message.get("tool_calls", [])

        if not tool_calls:
            # No tool calls → the model produced a text answer. We're done!
            return assistant_message.get("content", "")

        # ----- TOOL CALL DETECTED -----
        # Add the model's response (with tool calls) to conversation history
        messages.append(assistant_message)

        # Execute each requested tool and collect results
        for tool_call in tool_calls:
            fn_name = tool_call["function"]["name"]
            fn_args = tool_call["function"].get("arguments", {})

            print(f"  🔧 Agent is using tool: {fn_name}({fn_args})")

            # Look up and call the real Python function
            fn_to_call = TOOL_MAP.get(fn_name)
            if fn_to_call:
                result = fn_to_call(**fn_args)
            else:
                result = f"Error: Tool '{fn_name}' not found."

            # Add the tool result back into the conversation
            messages.append({
                "role": "tool",
                "content": result
            })
        # Loop back — the AI will now read the tool results and respond


def main():
    if not OLLAMA_API_KEY:
        print("❌ ERROR: Please open the .env file and add your OLLAMA_API_KEY.")
        return

    print(f"🤖 Starting V2 File Reading Agent (Model: {MODEL_NAME} via Ollama Cloud)")
    print("Try asking: 'What files are in the current directory?' or 'Read the .env file'")
    print("Type 'exit' to quit.\n")

    system_prompt = (
        "You are a helpful file assistant. "
        "You have tools to list and read files on the user's computer. "
        "Use them to answer file-related questions accurately."
    )

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
        if not user_input.strip():
            continue

        print("Agent is thinking...")
        try:
            response = run_agent(user_input, system_context=system_prompt)
            print(f"\nAgent: {response}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
        print("-" * 40)


if __name__ == "__main__":
    main()
