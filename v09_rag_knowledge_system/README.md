# V9 — RAG (Retrieval-Augmented Generation)

## 1. What Are We Building?

RAG is a technique that allows an AI application to answer questions using information from our own documents.

For example, imagine having 50 PDF files containing technical information. Instead of opening every PDF and searching manually, we can ask questions such as:

- Explain inheritance in Java using my documents.
- Find information about a particular technology.
- Summarize the main points from these files.
- Answer my question using the information in the documents.

The system finds relevant information from the documents and gives it to an AI model to generate an answer.

This is called **Retrieval-Augmented Generation (RAG)**.

## 2. How Does RAG Work?

RAG has two main stages.

### Stage 1: Preparing the Documents

1. Read the documents.
2. Divide them into smaller pieces called chunks.
3. Convert the chunks into numerical representations called embeddings.
4. Store the embeddings so that relevant information can be found later.

### Stage 2: Answering a Question

1. The user asks a question.
2. The system searches for relevant chunks.
3. It retrieves the most useful information.
4. The retrieved information is given to the AI model.
5. The AI model generates an answer using that information.

**Example:**

You provide a document about Java and ask, "What is inheritance?"

The system finds the relevant section about inheritance and gives it to the AI model. The model uses that information to generate an answer.

## 3. Important RAG Concepts

| Concept | Meaning in Simple English |
|---|---|
| Document loading | Reading information from documents. |
| Chunking | Dividing large documents into smaller pieces. |
| Embeddings | Converting text into numbers that represent its meaning. |
| Vector search | Finding text with a meaning similar to the user's question. |
| Vector database | Storing and searching embeddings. |
| Retrieval | Finding useful information from documents. |
| Prompting | Instructing the AI model how to answer. |
| Grounded answers | Answers based on retrieved information. |
| Evaluation | Checking whether retrieval and generated answers are correct. |

## 4. What Is Chunking?

Chunking means dividing a large document into smaller pieces.

Suppose a PDF contains 100 pages. Sending the entire document to an AI model for every question may be inefficient.

Instead, we divide it into smaller sections called chunks.

**Example: Java Programming Guide**

- Chunk 1: Introduction to Java
- Chunk 2: Variables and Data Types
- Chunk 3: Classes and Objects
- Chunk 4: Inheritance
- Chunk 5: Exception Handling

When the user asks about inheritance, the system can retrieve the relevant chunk instead of processing the entire document.

### 4.1 Different Chunking Methods

| Method | How It Works | When Should We Use It? |
|---|---|---|
| Fixed-size chunking | Splits text into pieces of a chosen size. | When we want a simple starting method. |
| Overlapping chunking | Allows neighboring chunks to share some text. | When important information may cross chunk boundaries. |
| Sentence-based chunking | Splits text at sentence boundaries. | When keeping complete sentences together matters. |
| Recursive chunking | Tries larger text boundaries first, then smaller ones if needed. | A good general starting point for many documents. |
| Structure-aware chunking | Uses headings, paragraphs, sections, or code structure. | When documents have a clear structure. |
| Semantic chunking | Groups text according to changes in meaning. | When preserving related ideas is important. |
| Parent-child chunking | Retrieves a small chunk but can provide its larger parent section as context. | When precise search results need additional context. |
| Agentic chunking | Uses an AI model to help decide how content should be divided. | When document structure is complex and simpler methods are insufficient. |

### 4.2 How Large Should a Chunk Be?

There is no single chunk size that works best for every document.

| Document Type | Starting Size to Experiment With |
|---|---|
| Short FAQs | 100–300 tokens |
| General articles | 300–600 tokens |
| Technical documentation | 500–1,000 tokens |
| Research papers | Split by sections, then adjust the size |
| Source code | Split by functions, classes, or logical blocks |

These are starting points, not fixed rules.

A **token** is a unit of text processed by a language model. One token is not always equal to one word.

Smaller chunks can provide precise information but may lose context. Larger chunks preserve more context but may include irrelevant information.

The best size depends on the document, the embedding model, and the questions users ask.

### 4.3 What Is Chunk Overlap?

Overlap means repeating a small part of one chunk in the next chunk.

For example, imagine a document divided into 500-token chunks with 50 tokens of overlap. The last 50 tokens of one chunk also appear at the beginning of the next.

This helps preserve information that crosses chunk boundaries.

Too much overlap creates unnecessary duplicate content and increases storage requirements.

### 4.4 How Do We Choose the Best Chunking Method?

Start with recursive chunking and a moderate chunk size.

Then compare different chunk sizes and methods using the same set of questions.

Check whether the system retrieves the correct information, whether important context is missing, and whether irrelevant content is returned.

## 5. What Are Embeddings?

Embeddings convert text into lists of numbers called vectors.

Consider these two sentences:

- "How can I learn Java?"
- "What is the best way to study Java?"

Although the words are different, their meanings are similar.

An embedding model converts each sentence into a numerical vector. The system can compare these vectors to find text with similar meanings.

### Important Embedding Concepts

| Concept | Meaning |
|---|---|
| Embedding model | The model that converts text into vectors. |
| Dense embeddings | Vectors containing many numerical values, where most values may be nonzero. |
| Sparse representations | Representations with many zero values, often useful for keyword-based retrieval. |
| Similarity metric | A calculation used to compare vectors. |
| Embedding dimensions | The number of numerical values in a vector. |
| Multilingual embeddings | Embeddings designed to represent text across multiple languages. |

### How Are Vectors Compared?

Common comparison methods include:

- **Cosine similarity:** Compares the direction of two vectors.
- **Dot product:** Multiplies corresponding values and adds the results.
- **Euclidean distance:** Measures the straight-line distance between two vectors.

Which method is best depends on the embedding model and how its vectors are intended to be compared.

**Important:** A high similarity score does not guarantee that the retrieved information is correct.

### How Do We Choose an Embedding Model?

Consider:

- Whether it supports the languages in our documents.
- Whether it performs well on our type of content.
- Its vector dimensions and context limits.
- Its retrieval accuracy.
- Whether it can run locally or requires an API.
- Its cost and usage limits.

The document embeddings and question embeddings must be compatible. If we change embedding models, we may need to generate the document embeddings again.

## 6. What Is a Vector Database?

A vector database stores embeddings and helps find vectors similar to a user's question.

Imagine having thousands of document chunks. Searching every chunk manually would be inefficient as the collection grows.

A vector database or vector-search index helps find relevant chunks efficiently.

### 6.1 Vector Databases

| Tool | What Is It? | When Should We Choose It, and Why? | Free Availability |
|---|---|---|---|
| Chroma | A vector database for AI applications. | A convenient starting point for small RAG projects and local experimentation. | Open-source; hosting and model costs are separate. |
| Qdrant | A vector database with vector search and metadata filtering. | When we need filtering and more control over retrieval. | Open-source self-hosted option; cloud plans may cost money. |
| Milvus | A vector database designed for large-scale vector search. | When exploring large collections and scalable vector-search systems. | Open-source self-hosted option; infrastructure costs apply. |
| Weaviate | A vector database with semantic search and integrations. | When we want built-in AI-oriented features and retrieval capabilities. | Open-source self-hosted option; managed services may cost money. |
| LanceDB | A database for vector and multimodal data workflows. | When exploring local-first retrieval and different types of data. | Open-source option; hosted services may cost money. |
| PostgreSQL + pgvector | PostgreSQL with vector-search capabilities. | When we want relational data and vector search in the same database. | Open-source; hosting costs depend on deployment. |
| Pinecone | A managed cloud vector database. | When we want a hosted service instead of managing the database ourselves. | Check current plans and free allowances. |
| Elasticsearch | A search engine that supports keyword and vector retrieval. | When combining full-text search, vector search, and filters. | Self-managed options exist; hosted services and features vary. |
| OpenSearch | An open-source search and analytics engine with vector capabilities. | When we need full-text and vector search in a search-oriented application. | Open-source self-hosted option; managed hosting may cost money. |
| Redis | A data platform that supports vector search. | When vector retrieval needs to work alongside caching and other Redis operations. | Availability and terms depend on the edition and deployment. |

### 6.2 Vector-Search Libraries

Not every vector-search tool is a database. Some are libraries that provide search and indexing functionality.

| Tool | What Is It? | When Should We Choose It? | Free Availability |
|---|---|---|---|
| FAISS | A library for efficient similarity search. | When learning vector indexes or building custom vector-search applications. | Open-source. |
| hnswlib | A library for approximate nearest-neighbor search. | When experimenting with HNSW indexing. | Open-source. |
| Annoy | A library for approximate nearest-neighbor search. | When exploring simple, read-heavy vector-search workloads. | Open-source. |
| ScaNN | A library for optimized vector similarity search. | When studying performance and accuracy trade-offs. | Open-source. |
| NumPy | A Python library for numerical calculations. | When learning how to compare vectors directly before using an index. | Open-source. |

A library such as FAISS can provide fast vector search, but you may need additional components for metadata management, persistence, access control, and other database features.

### 6.3 What Is a Vector Index?

A vector index helps the system find similar vectors without comparing every vector individually.

Some common indexing approaches are:

| Index | Simple Explanation | Main Trade-Off |
|---|---|---|
| Flat or exact search | Compares the query against every stored vector. | Accurate but can become slow for large collections. |
| IVF | Groups vectors into clusters and searches selected clusters. | Faster search, but may miss results if the search is too restrictive. |
| HNSW | Builds a graph that helps navigate toward nearby vectors. | Fast search, but uses additional memory and requires tuning. |
| Product Quantization (PQ) | Compresses vectors to reduce storage and memory requirements. | Saves memory but may reduce search accuracy. |

Different databases support different indexing methods and configurations.

You do not need to master these algorithms immediately. The important thing is to understand that vector indexing balances speed, memory, and retrieval accuracy.

### 6.4 How Do We Choose a Vector Database?

Consider:

- How much data we need to store.
- How fast searches must be.
- Whether we need metadata filtering.
- Whether keyword and vector search must work together.
- How much memory and storage are available.
- Whether we need local, self-hosted, or managed deployment.
- Whether the licensing and operating costs fit our requirements.

A small learning project does not need a distributed database. We can start with a simpler option and explore Milvus or other systems when scale or specific features justify it.

## 7. What Is Retrieval?

Retrieval means finding the document chunks most useful for answering a question.

The quality of retrieval strongly affects the quality of the final answer.

### 7.1 Different Retrieval Methods

| Method | How It Works | When Should We Use It? |
|---|---|---|
| Keyword search | Searches for matching words. | When exact names, IDs, or technical terms matter. |
| Vector search | Searches for similar meanings using embeddings. | When the question uses different words from the source document. |
| Hybrid search | Combines keyword search and vector search. | When both exact word matches and meaning are important. |
| Metadata filtering | Filters results using information such as document type or category. | When users need results from a particular group of documents. |
| Reranking | Reorders retrieved chunks according to their relevance to the question. | When the initial search returns several results of mixed quality. |
| Query rewriting | Rephrases the question to improve search. | When the original question is unclear or poorly suited to retrieval. |
| Multi-query retrieval | Generates alternative versions of a question and searches for each. | When one search might miss relevant information. |
| Parent-child retrieval | Finds a small chunk and then supplies a larger section for context. | When precise matches need additional explanation. |

These methods can be combined. For example, a system can use hybrid search, metadata filtering, and reranking in the same workflow.

## 8. How Do We Generate Grounded Answers?

After retrieval, the system gives the relevant chunks to the language model along with the user's question.

The model uses this information to generate an answer.

A good RAG system should:

- Use relevant retrieved information.
- Avoid inventing facts that are not supported by the documents.
- Include source references where possible.
- Handle conflicting information carefully.
- Admit when the available documents do not contain the answer.

Retrieval does not automatically make an AI answer correct. The quality of the documents, search results, instructions, and language model all matter.

## 9. What Is RAG Evaluation?

Evaluation means testing whether the system retrieves useful information and generates accurate answers.

A system can sound convincing while retrieving the wrong passage. That is why we should evaluate both retrieval and generation.

| Evaluation Method | What Does It Check? |
|---|---|
| Precision@K | How many of the top retrieved results are relevant? |
| Recall@K | How much of the relevant information appears in the top results? |
| MRR (Mean Reciprocal Rank) | How highly is the first relevant result ranked? |
| nDCG | Are relevant results ranked appropriately, including differences in relevance? |
| Faithfulness | Is the answer supported by the retrieved information? |
| Answer correctness | Does the answer match the known correct answer? |
| Citation correctness | Do the cited sources actually support the claims? |
| Latency | How long does retrieval and answer generation take? |

For a beginner project, we can start by creating a small set of questions with known answers and checking the retrieved chunks and final responses manually.

## 10. Different RAG Architectures

RAG can be designed in different ways depending on the application's needs.

| Architecture | Simple Explanation | When Should We Use It? |
|---|---|---|
| Basic RAG | Retrieves relevant chunks and sends them to an AI model. | As a starting point for document question-answering. |
| Hybrid RAG | Combines keyword and vector search. | When exact terms and semantic meaning both matter. |
| Reranking RAG | Reorders retrieved chunks before generating an answer. | When the initial retrieval results are not relevant enough. |
| Corrective RAG | Checks retrieval quality and takes corrective action when results are weak. | When poor retrieval could produce misleading answers. |
| Adaptive RAG | Changes its retrieval strategy depending on the question or situation. | When different questions need different levels of retrieval. |
| Agentic RAG | Allows an agent to decide how to search, which tools to use, or whether to search again. | When a question requires several searches or decisions. |
| GraphRAG | Uses relationships between entities and information in a graph alongside retrieval. | When questions require connections across many documents. |
| Multimodal RAG | Retrieves information from different data types, such as text and images. | When documents contain useful diagrams, images, or other media. |

These architectures are not mutually exclusive. A system may combine several of them.

Basic RAG is the foundation. Advanced designs should be introduced when they solve a real problem, rather than added simply because they are available.

## 11. RAG Frameworks and Tools

Frameworks provide reusable components for building RAG applications. They can simplify document processing, retrieval, model integration, and workflow management.

| Framework | When Should We Choose It, and Why? | Free Availability |
|---|---|---|
| LangChain | When we want reusable components for connecting language models, document loaders, retrievers, and tools. | Open-source; external model and hosting costs may apply. |
| LlamaIndex | When document ingestion and retrieval are central to the application. | Open-source; external model and hosting costs may apply. |
| Haystack | When we want structured pipelines for search, retrieval, and generation. | Open-source; deployment and model costs are separate. |
| LangGraph | When retrieval must be part of a stateful workflow with branching, retries, or agent decisions. | Open-source; external services may cost money. |
| Microsoft GraphRAG | When exploring graph-based retrieval and relationships across a document collection. | Open-source project; model and compute costs may apply. |
| LightRAG | When exploring graph-enhanced retrieval approaches. | Open-source project; model and infrastructure costs may apply. |
| RAGFlow | When exploring a more complete RAG platform with document processing and retrieval capabilities. | Open-source project; deployment and model costs may apply. |
| txtai | When we want a compact search and embeddings-oriented framework. | Open-source; external service costs may apply. |

**Important:** A framework, database, or library being open source does not mean every service connected to it is free. Model APIs, cloud hosting, and some managed or enterprise features may require payment. Check the current licence and service terms before choosing a tool.