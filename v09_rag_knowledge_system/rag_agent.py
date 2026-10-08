# ============================================================
# V9 - RAG KNOWLEDGE SYSTEM
# ============================================================
#
# What are we building?
#
# RAG = Retrieval-Augmented Generation
#
# The basic idea is:
#
#       DOCUMENT
#           ↓
#       CHUNKS
#           ↓
#      EMBEDDINGS
#           ↓
#      VECTOR STORE
#           ↓
#      USER QUESTION
#           ↓
#      RETRIEVE RELEVANT CHUNKS
#           ↓
#      SEND CONTEXT TO LLM
#           ↓
#         ANSWER
#
# In this version we are intentionally building the core RAG
# pipeline ourselves instead of using LangChain or LlamaIndex.
#
# This will help us understand what RAG actually does.
# ============================================================


# ============================================================
# STEP 1 - IMPORT REQUIRED LIBRARIES
# ============================================================

# os
# Used for working with file paths and environment variables.
import os

# json
# Used to save our vector store to a JSON file.
import json

# requests
# Used to communicate with the Ollama Cloud API.
import requests

# numpy
# Used for mathematical operations on embeddings/vectors.
import numpy as np

# load_dotenv
# Used to load values from our .env file.
from dotenv import load_dotenv


# ============================================================
# STEP 2 - LOAD ENVIRONMENT VARIABLES
# ============================================================

# This reads the .env file from the project.
load_dotenv()


# Read our Ollama API key.
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Read the Ollama API base URL.
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)

# Model used for generating the final answer.
MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemma4:31b"
)

# Model used for converting text into embeddings.
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "embeddinggemma"
)


# ============================================================
# STEP 3 - DEFINE FILE PATHS
# ============================================================

# Find the directory where this Python file is located.
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# Our knowledge document.
DOCUMENT_PATH = os.path.join(
    BASE_DIR,
    "agentic_ai_knowledge.txt"
)

# This file will contain our chunks and embeddings.
#
# We don't have to create this file manually.
# The program will create it.
VECTOR_STORE_PATH = os.path.join(
    BASE_DIR,
    "vector_store.json"
)


# ============================================================
# STEP 4 - BASIC VALIDATION
# ============================================================

# Make sure the API key exists.
if not OLLAMA_API_KEY:

    print("ERROR: OLLAMA_API_KEY was not found.")

    print(
        "Please check your .env file."
    )

    exit()


# Make sure our knowledge document exists.
if not os.path.exists(DOCUMENT_PATH):

    print(
        "ERROR: Knowledge document was not found:"
    )

    print(DOCUMENT_PATH)

    exit()


# ============================================================
# STEP 5 - CREATE HEADERS FOR OLLAMA CLOUD
# ============================================================

# Ollama Cloud requires authentication using our API key.
HEADERS = {
    "Authorization": f"Bearer {OLLAMA_API_KEY}",
    "Content-Type": "application/json"
}


# ============================================================
# STEP 6 - READ THE KNOWLEDGE DOCUMENT
# ============================================================

def load_document():
    """
    Read the entire knowledge document.

    Our source file is:

        agentic_ai_knowledge.txt

    The function returns the complete text.
    """

    print("\nLoading knowledge document...")

    with open(
        DOCUMENT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        text = file.read()

    print(
        f"Document loaded successfully."
    )

    print(
        f"Characters: {len(text)}"
    )

    return text


# ============================================================
# STEP 7 - SPLIT DOCUMENT INTO CHUNKS
# ============================================================

def create_chunks(
    text,
    chunk_size=500,
    overlap=100
):
    """
    Split a large document into smaller pieces.

    Why do we need chunks?

    Imagine our document has 20,000 words.

    We don't want to send all 20,000 words to the LLM
    every time the user asks one small question.

    Instead:

        Large document
              ↓
        Smaller chunks
              ↓
        Retrieve only useful chunks
              ↓
        Send those chunks to LLM

    chunk_size:
        Approximate number of words in each chunk.

    overlap:
        Number of words shared between neighboring chunks.

    Example:

        Chunk 1:
        A B C D E F G

        Chunk 2:
        F G H I J K L

    F and G are the overlap.

    This helps prevent losing context between chunks.
    """

    print("\nCreating document chunks...")

    # Convert the complete document into individual words.
    words = text.split()

    chunks = []

    # Start position of our first chunk.
    start = 0

    # Continue until we reach the end of the document.
    while start < len(words):

        # Calculate the end position.
        end = start + chunk_size

        # Take the words for this chunk.
        chunk_words = words[start:end]

        # Convert the words back into a string.
        chunk = " ".join(chunk_words)

        # Only save non-empty chunks.
        if chunk.strip():

            chunks.append(chunk)

        # Move forward.

        # We subtract overlap so that some words
        # are shared with the next chunk.
        start += chunk_size - overlap

    print(
        f"Created {len(chunks)} chunks."
    )

    return chunks


# ============================================================
# STEP 8 - CREATE EMBEDDING
# ============================================================

def create_embedding(text):
    """
    Convert text into a numerical vector.

    Example:

        "What is RAG?"

    becomes something conceptually like:

        [0.12, -0.43, 0.77, 0.21, ...]

    These numbers represent the meaning of the text
    in a mathematical vector space.

    We use the Ollama Cloud embedding API.
    """

    url = f"{OLLAMA_BASE_URL}/embed"

    payload = {
        "model": EMBEDDING_MODEL,
        "input": text
    }

    try:

        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=120
        )

        # If the API returned an error,
        # this will raise an exception.
        response.raise_for_status()

        data = response.json()

        # Ollama returns embeddings inside
        # the "embeddings" field.
        embedding = data["embeddings"][0]

        return embedding

    except requests.exceptions.RequestException as error:

        print("\nEmbedding API error:")
        print(error)

        # Try to display the API response.
        try:
            print(
                response.text
            )
        except:
            pass

        raise


# ============================================================
# STEP 9 - BUILD THE VECTOR STORE
# ============================================================

def build_vector_store(chunks):
    """
    Create embeddings for every document chunk.

    We store:

        chunk
        embedding
        chunk_id

    inside vector_store.json.

    This is our simple local vector database.

    In later versions we can replace this with
    Chroma, FAISS, Qdrant, etc.
    """

    print("\nBuilding vector store...")

    vector_store = []

    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks):

        print(
            f"Creating embedding "
            f"{index + 1}/{total_chunks}..."
        )

        # Convert the chunk into a vector.
        embedding = create_embedding(chunk)

        # Store the chunk and its vector.
        vector_store.append({

            "chunk_id": index,

            "text": chunk,

            "embedding": embedding

        })

    # Save the vector store to disk.
    with open(
        VECTOR_STORE_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            vector_store,
            file
        )

    print(
        "\nVector store created successfully."
    )

    print(
        f"Saved to: {VECTOR_STORE_PATH}"
    )

    return vector_store


# ============================================================
# STEP 10 - LOAD EXISTING VECTOR STORE
# ============================================================

def load_vector_store():
    """
    Load previously created embeddings.

    Why do we do this?

    We don't want to create embeddings every time
    the program starts.

    Embeddings can take time and API calls.

    Therefore:

        First run:
        Document
            ↓
        Create embeddings
            ↓
        Save vector_store.json

        Next runs:
        Load vector_store.json directly.
    """

    print(
        "\nLoading existing vector store..."
    )

    with open(
        VECTOR_STORE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        vector_store = json.load(file)

    print(
        f"Loaded {len(vector_store)} chunks."
    )

    return vector_store


# ============================================================
# STEP 11 - CALCULATE COSINE SIMILARITY
# ============================================================

def cosine_similarity(vector_a, vector_b):
    """
    Calculate cosine similarity between two vectors.

    Why?

    We need to determine:

        How similar is the user's question
        to each document chunk?

    Example:

        Question:
        "What is RAG?"

        Chunk A:
        Information about RAG

        Chunk B:
        Information about Git

    Chunk A should have a higher similarity score.

    Cosine similarity returns a score based on
    the direction of the vectors.
    """

    # Convert lists into NumPy arrays.
    a = np.array(
        vector_a,
        dtype=np.float32
    )

    b = np.array(
        vector_b,
        dtype=np.float32
    )

    # Calculate the dot product.
    dot_product = np.dot(a, b)

    # Calculate vector magnitudes.
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    # Avoid division by zero.
    if norm_a == 0 or norm_b == 0:

        return 0.0

    # Cosine similarity formula.
    similarity = (
        dot_product /
        (norm_a * norm_b)
    )

    return float(similarity)


# ============================================================
# STEP 12 - SEARCH THE VECTOR STORE
# ============================================================

def search_vector_store(
    question,
    vector_store,
    top_k=5
):
    """
    Find the most relevant chunks for a question.

    Steps:

    1. Convert question into an embedding.
    2. Compare question embedding against every chunk.
    3. Calculate similarity scores.
    4. Sort chunks by similarity.
    5. Return the best chunks.

    top_k=5 means:

        Return the 5 most relevant chunks.
    """

    print(
        "\nSearching knowledge base..."
    )

    # Create an embedding for the user's question.
    question_embedding = create_embedding(
        question
    )

    scored_chunks = []

    # Compare question against every stored chunk.
    for item in vector_store:

        similarity = cosine_similarity(

            question_embedding,

            item["embedding"]

        )

        scored_chunks.append({

            "chunk_id": item["chunk_id"],

            "text": item["text"],

            "score": similarity

        })

    # Sort by similarity score.
    #
    # reverse=True means highest score first.
    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # Return only the top K results.
    top_results = scored_chunks[:top_k]

    return top_results


# ============================================================
# STEP 13 - DISPLAY RETRIEVED CHUNKS
# ============================================================

def display_retrieved_chunks(results):
    """
    Display the chunks retrieved from the knowledge base.

    This is extremely useful while learning RAG.

    It allows us to SEE what information was given
    to the LLM.

    Later, we could hide this from the normal user.
    """

    print(
        "\n================ RETRIEVED CHUNKS ================"
    )

    for index, result in enumerate(results):

        print(
            f"\n--- Result {index + 1} ---"
        )

        print(
            f"Chunk ID: {result['chunk_id']}"
        )

        print(
            f"Similarity: {result['score']:.4f}"
        )

        print(
            f"\n{result['text']}"
        )

    print(
        "\n==================================================="
    )


# ============================================================
# STEP 14 - BUILD RAG PROMPT
# ============================================================

def build_rag_prompt(
    question,
    retrieved_chunks
):
    """
    Build the prompt that will be sent to Gemma.

    Important:

    We are NOT asking the model to answer only from
    its general knowledge.

    We explicitly provide the retrieved context.

    This is the "Augmented" part of:

        Retrieval-Augmented Generation
    """

    # Combine all retrieved chunks.
    context_parts = []

    for index, result in enumerate(
        retrieved_chunks
    ):

        context_parts.append(

            f"""
SOURCE {index + 1}

{result['text']}
"""

        )

    # Combine all sources into one context string.
    context = "\n".join(
        context_parts
    )

    # Build the final prompt.
    prompt = f"""
You are a helpful RAG knowledge assistant.

Your job is to answer the user's question using
the provided knowledge base context.

IMPORTANT RULES:

1. Use the provided context as the primary source.
2. Do not invent information that is not supported
   by the context.
3. If the context does not contain enough information,
   clearly say that the information was not found
   in the knowledge base.
4. Explain the answer in simple English.
5. You may combine information from multiple sources
   if they are relevant.

================ KNOWLEDGE BASE CONTEXT ================

{context}

================ END CONTEXT ============================

USER QUESTION:

{question}

==========================================================

Answer the user's question based on the knowledge base.
"""

    return prompt


# ============================================================
# STEP 15 - ASK OLLAMA TO GENERATE THE ANSWER
# ============================================================

def generate_answer(prompt):
    """
    Send our RAG prompt to the Ollama Cloud LLM.

    The LLM receives:

        System instructions
        +
        Retrieved document context
        +
        User question

    It then generates the final answer.
    """

    url = f"{OLLAMA_BASE_URL}/chat"

    payload = {

        "model": MODEL_NAME,

        "messages": [

            {
                "role": "user",

                "content": prompt
            }

        ],

        "stream": False

    }

    try:

        response = requests.post(

            url,

            headers=HEADERS,

            json=payload,

            timeout=120

        )

        response.raise_for_status()

        data = response.json()

        # Extract the generated answer.
        answer = data["message"]["content"]

        return answer

    except requests.exceptions.RequestException as error:

        print(
            "\nLLM API error:"
        )

        print(error)

        try:

            print(
                response.text
            )

        except:

            pass

        return None


# ============================================================
# STEP 16 - PROCESS ONE USER QUESTION
# ============================================================

def ask_question(
    question,
    vector_store
):
    """
    Complete RAG pipeline for one question.

    This function connects everything together:

        Question
           ↓
        Embedding
           ↓
        Retrieval
           ↓
        Context
           ↓
        Prompt
           ↓
        LLM
           ↓
        Answer
    """

    # --------------------------------------------------------
    # RETRIEVAL
    # --------------------------------------------------------

    results = search_vector_store(
        question,
        vector_store,
        top_k=5
    )

    # Show what the retriever found.
    display_retrieved_chunks(
        results
    )

    # --------------------------------------------------------
    # PROMPT CONSTRUCTION
    # --------------------------------------------------------

    prompt = build_rag_prompt(
        question,
        results
    )

    # --------------------------------------------------------
    # GENERATION
    # --------------------------------------------------------

    print(
        "\nGenerating answer..."
    )

    answer = generate_answer(
        prompt
    )

    # --------------------------------------------------------
    # DISPLAY FINAL ANSWER
    # --------------------------------------------------------

    print(
        "\n================ ANSWER ================="
    )

    if answer:

        print(answer)

    else:

        print(
            "Unable to generate an answer."
        )

    print(
        "========================================="
    )


# ============================================================
# STEP 17 - MAIN PROGRAM
# ============================================================

def main():

    print(
        "\n================================================"
    )

    print(
        "       V9 - RAG KNOWLEDGE SYSTEM"
    )

    print(
        "================================================"
    )

    print(
        f"\nLLM Model: {MODEL_NAME}"
    )

    print(
        f"Embedding Model: {EMBEDDING_MODEL}"
    )

    print(
        f"Knowledge Base: {DOCUMENT_PATH}"
    )

    # --------------------------------------------------------
    # LOAD DOCUMENT
    # --------------------------------------------------------

    document = load_document()

    # --------------------------------------------------------
    # CREATE OR LOAD VECTOR STORE
    # --------------------------------------------------------

    if os.path.exists(
        VECTOR_STORE_PATH
    ):

        # Vector store already exists.
        #
        # This means we don't need to recreate
        # all embeddings.
        vector_store = load_vector_store()

    else:

        # First run.
        #
        # We need to:
        #
        # 1. Split document
        # 2. Create embeddings
        # 3. Save vector store

        chunks = create_chunks(
            document,
            chunk_size=500,
            overlap=100
        )

        vector_store = build_vector_store(
            chunks
        )

    # --------------------------------------------------------
    # START INTERACTIVE CHAT
    # --------------------------------------------------------

    print(
        "\nRAG system is ready!"
    )

    print(
        "\nAsk questions about the knowledge base."
    )

    print(
        "Type 'exit' to stop."
    )

    # Infinite loop for questions.
    while True:

        try:

            question = input(
                "\nYou: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print(
                "\nGoodbye!"
            )

            break

        # Ignore empty questions.
        if not question:

            continue

        # Exit command.
        if question.lower() in [
            "exit",
            "quit"
        ]:

            print(
                "\nGoodbye!"
            )

            break

        # Process the question through RAG.
        ask_question(
            question,
            vector_store
        )


# ============================================================
# STEP 18 - START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()