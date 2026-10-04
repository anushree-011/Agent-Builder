import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------
# CONCEPT 1: ENVIRONMENT & API KEYS
# ---------------------------------------------------------
# We use python-dotenv to load the GEMINI_API_KEY from our .env file.
# The Gemini SDK automatically looks for the GEMINI_API_KEY environment variable.
load_dotenv()

# We specify the model we want to use. gemini-2.5-flash is fast and great for general agents.
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

# Initialize the Gemini client
# It will automatically pick up the GEMINI_API_KEY from the environment
client = genai.Client()

def ask_llm(prompt_text, system_context=""):
    """
    Sends a prompt to the Gemini API and gets a response.
    
    Parameters:
    - prompt_text: The actual question or task from the user.
    - system_context: Background rules or persona instructions for the AI.
    """
    
    # ---------------------------------------------------------
    # CONCEPT 2: PROMPTS AND CONFIGURATION
    # ---------------------------------------------------------
    # We configure the request by setting the system instructions.
    # The SDK allows us to pass a config object with these rules.
    config = types.GenerateContentConfig(
        system_instruction=system_context,
        temperature=0.7 # Optional: Controls how creative/random the output is (0.0 to 2.0)
    )
    
    try:
        # We send the request to Google's servers
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt_text,
            config=config
        )
        return response.text
        
    except Exception as e:
        return f"An error occurred: {e}"

def main():
    # Make sure the API key is actually set before starting
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        print("❌ ERROR: Please open the .env file and add your real GEMINI_API_KEY.")
        return

    print(f"🤖 Starting V1 Agent (Powered by {MODEL_NAME})")
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
