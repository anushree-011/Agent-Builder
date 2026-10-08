"""
============================================================
V9 - RAG KNOWLEDGE SYSTEM
============================================================

This version teaches:

1. Document loading
2. Text chunking
3. Embeddings
4. Vector storage
5. Similarity search
6. Retrieval
7. Grounded generation
8. Ollama Cloud integration

Architecture:

Knowledge Base
      ↓
   Chunking
      ↓
 Embedding Model
      ↓
 Vector Store
      ↓
 User Question
      ↓
 Question Embedding
      ↓
 Similarity Search
      ↓
 Relevant Chunks
      ↓
 Ollama Cloud
      ↓
 Final Answer
============================================================
"""

import os
import json
import requests

import numpy as np

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


# ============================================================
# STEP 1 - LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "https://ollama.com/api"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemma4:31b"
)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5"
)


# ============================================================
# STEP 2 - FILE PATHS
# ============================================================

# Folder containing this Python file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Knowledge base file
KNOWLEDGE_FILE = os.path.join(
    BASE_DIR,
    "agentic_ai_knowledge.txt"
)


# Vector store file
VECTOR_STORE_FILE = os.path.join(
    BASE_DIR,
    "vector_store.json"
)


# ============================================================
# STEP 3 - RAG SETTINGS
# ============================================================

# Number of words in each chunk
CHUNK_SIZE = 500


# Number of overlapping words between chunks
CHUNK_OVERLAP = 100


# Number of relevant chunks retrieved
TOP_K = 5


# Minimum similarity required
SIMILARITY_THRESHOLD = 0.35


# ============================================================
# STEP 4 - DISPLAY CONFIGURATION
# ============================================================

print()
print("=" * 60)
print("        V9 - RAG KNOWLEDGE SYSTEM")
print("=" * 60)

print()
print("LLM:")
print(f"  {MODEL_NAME}")

print()
print("Embedding Model:")
print(f"  {EMBEDDING_MODEL_NAME}")

print()
print("Knowledge Base:")
print(f"  {KNOWLEDGE_FILE}")

print()


# ============================================================
# STEP 5 - CHECK OLLAMA API KEY
# ============================================================

if not OLLAMA_API_KEY:

    print("ERROR:")
    print("OLLAMA_API_KEY is missing from .env")

    exit()


# ============================================================
# STEP 6 - LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")
print(f"Model: {EMBEDDING_MODEL_NAME}")
print()

print(
    "IMPORTANT:"
)
print(
    "The first run may take time because the embedding model"
)
print(
    "needs to be downloaded."
)
print()


embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)


print("Embedding model loaded successfully.")
print()


# ============================================================
# STEP 7 - LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():
    """
    Read the knowledge base text file.
    """

    if not os.path.exists(KNOWLEDGE_FILE):

        raise FileNotFoundError(
            f"Knowledge file not found: {KNOWLEDGE_FILE}"
        )

    with open(
        KNOWLEDGE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        text = file.read()

    return text


# ============================================================
# STEP 8 - SPLIT DOCUMENT INTO CHUNKS
# ============================================================

def create_chunks(text):
    """
    Split the knowledge base into overlapping word chunks.

    Example:

    Chunk 1:
    words 1 - 500

    Chunk 2:
    words 401 - 900

    Chunk 3:
    words 801 - 1300
    """

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + CHUNK_SIZE

        chunk_words = words[start:end]

        chunk = " ".join(chunk_words)

        if chunk.strip():

            chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ============================================================
# STEP 9 - CREATE EMBEDDINGS
# ============================================================

def create_embeddings(chunks):
    """
    Convert each text chunk into an embedding vector.

    normalize_embeddings=True makes cosine similarity
    easier because we can use a dot product.
    """

    print("Creating embeddings...")
    print(f"Number of chunks: {len(chunks)}")
    print()

    embeddings = embedding_model.encode(
        chunks,
        batch_size=8,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embeddings


# ============================================================
# STEP 10 - SAVE VECTOR STORE
# ============================================================

def save_vector_store(chunks, embeddings):
    """
    Save chunks and their embeddings to JSON.

    This allows us to reuse the embeddings instead of
    creating them every time the program starts.
    """

    data = []

    for index, chunk in enumerate(chunks):

        data.append(
            {
                "id": index,
                "text": chunk,
                "embedding": embeddings[index].tolist()
            }
        )

    with open(
        VECTOR_STORE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file
        )

    print()
    print("Vector store saved:")
    print(VECTOR_STORE_FILE)


# ============================================================
# STEP 11 - LOAD VECTOR STORE
# ============================================================

def load_vector_store():
    """
    Load previously created vectors.
    """

    with open(
        VECTOR_STORE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    chunks = [
        item["text"]
        for item in data
    ]

    embeddings = np.array(
        [
            item["embedding"]
            for item in data
        ],
        dtype=np.float32
    )

    return chunks, embeddings


# ============================================================
# STEP 12 - BUILD OR LOAD VECTOR STORE
# ============================================================

def prepare_vector_store():

    if os.path.exists(VECTOR_STORE_FILE):

        print("Existing vector store found.")
        print("Loading vector store...")
        print()

        chunks, embeddings = load_vector_store()

        print(
            f"Loaded {len(chunks)} chunks."
        )

        return chunks, embeddings

    print("No vector store found.")
    print("Building a new vector store...")
    print()

    knowledge = load_knowledge_base()

    chunks = create_chunks(
        knowledge
    )

    print(
        f"Created {len(chunks)} chunks."
    )

    embeddings = create_embeddings(
        chunks
    )

    save_vector_store(
        chunks,
        embeddings
    )

    return chunks, embeddings


# ============================================================
# STEP 13 - CREATE QUERY EMBEDDING
# ============================================================

def create_query_embedding(question):
    """
    Convert the user's question into an embedding.
    """

    embedding = embedding_model.encode(
        question,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embedding


# ============================================================
# STEP 14 - SEARCH FOR RELEVANT CHUNKS
# ============================================================

def search_knowledge(
    question,
    chunks,
    embeddings
):
    """
    Find the chunks most similar to the question.

    Because both vectors are normalized:

        cosine similarity
              =
        dot product
    """

    query_embedding = create_query_embedding(
        question
    )

    similarities = np.dot(
        embeddings,
        query_embedding
    )

    # Sort from highest similarity to lowest
    ranked_indices = np.argsort(
        similarities
    )[::-1]

    results = []

    for index in ranked_indices[:TOP_K]:

        score = float(
            similarities[index]
        )

        if score >= SIMILARITY_THRESHOLD:

            results.append(
                {
                    "text": chunks[index],
                    "score": score
                }
            )

    return results


# ============================================================
# STEP 15 - DISPLAY RETRIEVED INFORMATION
# ============================================================

def display_retrieved_chunks(results):

    print()
    print("=" * 60)
    print("RETRIEVED KNOWLEDGE")
    print("=" * 60)

    if not results:

        print(
            "No sufficiently relevant knowledge found."
        )

        return

    for index, result in enumerate(
        results,
        start=1
    ):

        print()
        print(
            f"CHUNK {index}"
        )

        print(
            f"Similarity: {result['score']:.4f}"
        )

        print("-" * 60)

        print(
            result["text"]
        )


# ============================================================
# STEP 16 - CREATE RAG PROMPT
# ============================================================

def create_rag_prompt(
    question,
    results
):
    """
    Create the final prompt sent to the LLM.

    The LLM is instructed to answer using the retrieved
    knowledge instead of inventing information.
    """

    if not results:

        context = "No relevant knowledge was found."

    else:

        context_parts = []

        for index, result in enumerate(
            results,
            start=1
        ):

            context_parts.append(
                f"""
--- Knowledge Chunk {index} ---
{result["text"]}
"""
            )

        context = "\n".join(
            context_parts
        )

    prompt = f"""
You are a helpful AI assistant.

Answer the user's question using the provided knowledge.

IMPORTANT RULES:

1. Use the provided knowledge as the primary source.
2. Do not invent facts that are not supported by the knowledge.
3. If the knowledge does not contain enough information,
   clearly say that the knowledge base does not contain
   enough information to answer.
4. Give a simple and clear answer.
5. Do not mention internal RAG processing unless necessary.

KNOWLEDGE:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    return prompt


# ============================================================
# STEP 17 - CALL OLLAMA CLOUD
# ============================================================

def ask_ollama(prompt):
    """
    Send the RAG prompt to Ollama Cloud.
    """

    url = f"{OLLAMA_BASE_URL}/chat"

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

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

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]


# ============================================================
# STEP 18 - ASK A QUESTION
# ============================================================

def answer_question(
    question,
    chunks,
    embeddings
):

    # --------------------------------------------
    # Retrieve relevant knowledge
    # --------------------------------------------

    results = search_knowledge(
        question,
        chunks,
        embeddings
    )

    # --------------------------------------------
    # Show retrieved chunks
    # --------------------------------------------

    display_retrieved_chunks(
        results
    )

    # --------------------------------------------
    # Create RAG prompt
    # --------------------------------------------

    prompt = create_rag_prompt(
        question,
        results
    )

    # --------------------------------------------
    # Send prompt to Ollama
    # --------------------------------------------

    print()
    print("=" * 60)
    print("GENERATING ANSWER")
    print("=" * 60)
    print()

    answer = ask_ollama(
        prompt
    )

    return answer


# ============================================================
# STEP 19 - MAIN PROGRAM
# ============================================================

def main():

    # --------------------------------------------
    # Prepare vector database
    # --------------------------------------------

    chunks, embeddings = prepare_vector_store()

    print()
    print("=" * 60)
    print("V9 RAG SYSTEM READY")
    print("=" * 60)

    print()
    print(
        "Type your question."
    )

    print(
        "Type 'exit' to stop."
    )

    # --------------------------------------------
    # Interactive question loop
    # --------------------------------------------

    while True:

        try:

            question = input(
                "\nYou: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()
            print("Exiting...")
            break

        if question.lower() == "exit":

            print(
                "Goodbye!"
            )

            break

        if not question:

            continue

        try:

            answer = answer_question(
                question,
                chunks,
                embeddings
            )

            print()
            print("=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)

            print()
            print(answer)

        except requests.exceptions.RequestException as error:

            print()
            print("Ollama API error:")
            print(error)

        except Exception as error:

            print()
            print("ERROR:")
            print(error)


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()