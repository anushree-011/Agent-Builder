import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
client = genai.Client()

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
# The Gemini API doesn't know our Python functions exist.
# We have to describe each tool to it in a structured format.
# This description is called a "schema".
# The AI reads these schemas to understand:
#   - WHAT each tool is called
#   - WHAT it does (the description)
#   - WHAT parameters to send (and their types)

list_files_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="list_files",
            description="Lists all files and folders inside a given directory path on the user's computer.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "directory": types.Schema(
                        type=types.Type.STRING,
                        description="The path of the directory to list. Defaults to the current directory '.'",
                    )
                },
            ),
        )
    ]
)

read_file_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="read_file",
            description="Reads and returns the full text content of a file from the user's computer.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "filepath": types.Schema(
                        type=types.Type.STRING,
                        description="The full or relative path to the file to be read.",
                    )
                },
                required=["filepath"],
            ),
        )
    ]
)

# We group all tools together so we can pass them to the API
ALL_TOOLS = [list_files_tool, read_file_tool]

# A lookup map so we can find and call the right Python function
# when the AI requests a specific tool by name
TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
}


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
    config = types.GenerateContentConfig(
        system_instruction=system_context,
        tools=ALL_TOOLS,  # <-- We give the AI the list of tools it can use
        temperature=0.2,  # Low temperature = more focused, less creative
    )

    # Start the conversation with the user's task
    messages = [types.Content(role="user", parts=[types.Part(text=task)])]

    # The agent loop — keeps going until the model gives a text reply
    while True:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=messages,
            config=config,
        )

        candidate = response.candidates[0].content

        # Check if the model wants to call a tool
        tool_calls = [p for p in candidate.parts if p.function_call]

        if not tool_calls:
            # No tool calls → the model produced a text answer. We're done!
            return response.text

        # ----- TOOL CALL DETECTED -----
        # Add the model's tool request to the conversation history
        messages.append(candidate)

        # Execute each requested tool and collect results
        function_responses = []
        for part in tool_calls:
            fn_name = part.function_call.name
            fn_args = dict(part.function_call.args)

            print(f"  🔧 Agent is using tool: {fn_name}({fn_args})")

            # Look up and call the real Python function
            fn_to_call = TOOL_MAP.get(fn_name)
            if fn_to_call:
                result = fn_to_call(**fn_args)
            else:
                result = f"Error: Tool '{fn_name}' not found."

            function_responses.append(
                types.Part.from_function_response(
                    name=fn_name,
                    response={"result": result}
                )
            )

        # Add the tool results back into the conversation so the AI can see them
        messages.append(types.Content(role="user", parts=function_responses))
        # Loop back — the AI will now read the tool results and respond


def main():
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        print("❌ ERROR: Please open the .env file and add your real GEMINI_API_KEY.")
        return

    print(f"🤖 Starting V2 File Reading Agent (Model: {MODEL_NAME})")
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
        response = run_agent(user_input, system_context=system_prompt)
        print(f"\nAgent: {response}\n")
        print("-" * 40)


if __name__ == "__main__":
    main()
