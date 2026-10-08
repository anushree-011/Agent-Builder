import os
import time
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------
# CONCEPT 1: ENVIRONMENT & API KEYS
# ---------------------------------------------------------
# We use python-dotenv to load the OLLAMA_API_KEY from our .env file.
load_dotenv()

# We specify the model we want to use.
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:31b")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api")

def ask_llm(prompt_text, system_context=""):
    """
    Sends a prompt to the Ollama Cloud API and gets a response.
    
    Parameters:
    - prompt_text: The actual question or task from the user.
    - system_context: Background rules or persona instructions for the AI.
    """
    
    # ---------------------------------------------------------
    # CONCEPT 2: PROMPTS AND CONFIGURATION
    # ---------------------------------------------------------
    # We build the messages list with an optional system prompt
    # and the user's message, then send it to the Ollama API.
    messages = []
    if system_context:
        messages.append({"role": "system", "content": system_context})
    messages.append({"role": "user", "content": prompt_text})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7  # Controls how creative/random the output is
        }
    }

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
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except Exception as e:
            if attempt < max_retries and ("503" in str(e) or "504" in str(e) or "timeout" in str(e).lower()):
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                print(f"  ⏳ Model busy, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                return f"An error occurred: {e}"

def main():
    # Make sure the API key is actually set before starting
    if not OLLAMA_API_KEY:
        print("❌ ERROR: Please open the .env file and add your OLLAMA_API_KEY.")
        return

    print(f"🤖 Starting V1 Agent (Powered by {MODEL_NAME} via Ollama Cloud)")
    print("Type 'exit' to quit.\n")
    
    # ---------------------------------------------------------
    # CONCEPT 3: CONTEXT (System Prompt)
    # ---------------------------------------------------------
    # This is the "hidden" set of instructions given to the LLM before it sees the user task.
    # It defines the agent's behavior, tone, and constraints.
    system_prompt = (
        "You are a helpful, concise AI agent. "
        "Answer questions directly and do not use more than 3 sentences unless necessary."
    )
    
    # ---------------------------------------------------------
    # CONCEPT 4: THE AGENT LOOP
    # ---------------------------------------------------------
    # An agent isn't a one-off script; it's a continuously running loop that:
    # 1. Observes (Gets user input)
    # 2. Thinks (Calls the LLM)
    # 3. Acts (Prints the response)
    while True:
        # Step 1: Observe (Get Task)
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
            
        if not user_input.strip():
            continue
            
        print("Agent is thinking...")
        
        # Step 2: Think (Call LLM)
        response = ask_llm(user_input, system_context=system_prompt)
        
        # Step 3: Act (Respond)
        print(f"\nAgent: {response}\n")
        print("-" * 40)

if __name__ == "__main__":
    main()
