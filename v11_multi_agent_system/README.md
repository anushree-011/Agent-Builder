# V11 — Multi-Agent System

## Overview
**Multi-Agent Systems (MAS)** represent the next architectural evolution beyond single-turn routing (v10). Instead of delegating a single user request to one agent, a **Coordinator Agent** decomposes complex user goals into an ordered sequence of interdependent steps, invokes specialized agents, and uses a **Shared State (Blackboard)** for inter-agent communication and final response synthesis.

---

## Architecture Diagram

```
                              ┌──────────────────────┐
                              │     User Request     │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  Coordinator Agent   │
                              │ (Task Decomposition) │
                              └──────────┬───────────┘
                                         │
                        Creates Execution Plan: Step 1 -> Step 2 -> Step 3
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              ▼                          ▼                          ▼
     ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
     │   File Agent    │        │  Memory Agent   │        │Calculator Agent │
     └────────┬────────┘        └────────┬────────┘        └────────┬────────┘
              │                          │                          │
              └──────────────────┐       │       ┌──────────────────┘
                                 ▼       ▼       ▼
                     ┌──────────────────────────────────────┐
                     │         Shared State Store           │
                     │  - Original Goal                     │
                     │  - Chronological Agent Results       │
                     │  - Completed Agent Registry          │
                     └──────────────────┬───────────────────┘
                                        │
                                        ▼
                     ┌──────────────────────────────────────┐
                     │          Final Synthesis             │
                     │  (Coordinator synthesizes summary)   │
                     └──────────────────────────────────────┘
```

---

## Core Components

### 1. Task Decomposition & Planning (`coordinator_agent.py`)
The Coordinator inspects the user's objective and decomposes it into discrete steps represented in JSON:
```json
{
  "steps": [
    {"agent": "FILE_AGENT", "task": "Create folder Projects/V11"},
    {"agent": "FILE_AGENT", "task": "Create Projects/V11/notes.txt with content 'Initial release'"},
    {"agent": "MEMORY_AGENT", "task": "Remember that Projects/V11 was initialized"},
    {"agent": "CALCULATOR_AGENT", "task": "Calculate 15 * 8"}
  ]
}
```

### 2. Blackboard / Shared State (`shared_state.py`)
Maintains a shared memory container where each specialist can publish its findings and downstream specialists can reference prior context.
- Stores `task`: original user objective.
- Stores `results`: list of `{"agent": name, "result": output}` entries.
- Stores `completed_agents`: tracking execution progress.

### 3. Context-Aware Specialist Agents (`agents.py`)
Each specialist agent receives both its specific subtask and the full `shared_state`. This allows agents to resolve dependencies dynamically without human intervention.

### 4. Final Synthesis
Once all steps are executed, the Coordinator reviews the accumulated blackboard state and generates a concise, consolidated final answer for the user.

---

## File Structure

| File | Description |
| :--- | :--- |
| `coordinator_agent.py` | Orchestrator responsible for task decomposition, step execution, and final synthesis. |
| `shared_state.py` | Blackboard state container shared between all participating agents. |
| `agents.py` | Context-aware File, Memory, and Calculator specialist agents. |
| `tools.py` | Safe concrete tools for file I/O, memory operations, and AST calculation. |
| `main.py` | Interactive CLI interface for user interaction with the multi-agent system. |

---

## How to Run

```powershell
# Navigate to the folder
cd v11_multi_agent_system

# Launch the multi-agent system CLI
python main.py
```

### Example Multi-Step Prompt
> *"Create a directory named Research, write a summary file inside it titled roadmap.md, remember that the roadmap was created, and calculate 25 * 4."*

1. **Step 1 (File Agent)**: Creates directory `Research`.
2. **Step 2 (File Agent)**: Creates file `Research/roadmap.md`.
3. **Step 3 (Memory Agent)**: Records memory item with shared context.
4. **Step 4 (Calculator Agent)**: Evaluates `25 * 4 = 100`.
5. **Coordinator Synthesis**: Produces a structured summary confirming all 4 completed actions.
