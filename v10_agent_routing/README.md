# V10 — Agent Routing System

## Overview
**Agent Routing** is an architectural pattern in Agentic AI where a central supervisory model (**Router Agent**) inspects user input, detects the intent, and delegates execution to a domain-specific **Specialist Agent** rather than trying to handle every capability within one single prompt.

---

## Architecture Diagram

```
                       ┌──────────────────────┐
                       │     User Request     │
                       └──────────┬───────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │     Router Agent     │
                       │(Intent Classification│
                       └──────────┬───────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│    File Agent    │    │   Memory Agent   │    │ Calculator Agent │
│  (Files/Folders) │    │(Recall / Search) │    │  (Safe Math AST) │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│    File Tools    │    │   Memory Tools   │    │  AST Calculator  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## Core Concepts

### 1. Intent Detection
The Router Agent analyzes user input and outputs a strict JSON object specifying which specialist should handle the task:
```json
{"agent": "FILE_AGENT"}
```
Possible routing outputs:
- `FILE_AGENT`: Creating, reading, listing files and folders.
- `MEMORY_AGENT`: Storing facts, recalling memories, searching past information.
- `CALCULATOR_AGENT`: Safe arithmetic expressions.
- `NONE`: Irrelevant or unroutable prompts.

### 2. Specialist Delegation
Each specialist agent has a dedicated, constrained system prompt exposing only tools relevant to its domain. This dramatically decreases token consumption and eliminates hallucinations.

### 3. Safe Execution
- Mathematical expressions are parsed into an Abstract Syntax Tree (`ast.parse`) with whitelisted operators, never using insecure `eval()`.
- Directory operations are verified to prevent path traversal issues.

---

## File Structure

| File | Description |
| :--- | :--- |
| `router_agent.py` | Intent classification model, JSON extraction, and specialist delegation. |
| `specialist_agents.py` | Implementations of File Agent, Memory Agent, and Calculator Agent. |
| `tools.py` | Safe tools for file handling, memory persistence, and AST calculation. |
| `main.py` | Interactive CLI REPL loop for user interaction. |

---

## How to Run

```powershell
# Navigate to the folder
cd v10_agent_routing

# Run the routing agent
python main.py
```

### Example Interactions
- **File Agent**: *"Create a folder called test_docs"* -> Routes to `FILE_AGENT` -> Creates folder.
- **Memory Agent**: *"Remember that our project deadline is Friday"* -> Routes to `MEMORY_AGENT` -> Stores memory.
- **Calculator Agent**: *"Calculate 144 / 12 + 50"* -> Routes to `CALCULATOR_AGENT` -> Computes `62.0`.
