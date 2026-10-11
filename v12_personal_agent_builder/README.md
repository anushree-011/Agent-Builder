# V12 — Personal Agent Builder

## Overview
**Personal Agent Builder** is the capstone framework of the Agent-Builder learning path. It consolidates all foundational and advanced patterns explored across versions 1 through 11 into a unified, modular, and configurable agent development architecture.

> **Core Concept:** A Configurable Agent Engine. You define what kind of agent you want (Goal, Persona, Tools, Memory, Safety Guardrails, Planning, Reflection), and the Builder dynamically configures and instantiates it!

---

## Architectural Synthesis

```
                               ┌────────────────────────────────┐
                               │  User Agent Specification      │
                               │  - "Build a coding agent with  │
                               │    file access and approval"   │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │    AgentBuilder / Meta-Builder   │
                              │    (Fluent Configuration Engine) │
                              └────────────────┬─────────────────┘
                                               │
                  ┌────────────────────────────┼────────────────────────────┐
                  │                            │                            │
                  ▼                            ▼                            ▼
        ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
        │  Tools Registry  │         │  Dual Memory     │         │ Safety & HITL    │
        │ - Files (r/w/ls) │         │ - Working Buffer │         │ - Permissive     │
        │ - AST Calculator │         │ - File Persistent│         │ - Moderate       │
        │ - Custom Tools   │         │   Fact Storage   │         │ - Strict Approval│
        └─────────┬────────┘         └─────────┬────────┘         └─────────┬────────┘
                  │                            │                            │
                  └────────────────────────────┼────────────────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │      PersonalAgent Runtime       │
                              │  - Multi-Step Planning (v04)     │
                              │  - Tool Invocation & ReAct (v05) │
                              │  - Safety Interception (v07)     │
                              │  - Self-Evaluation/Reflect (v08) │
                              └──────────────────────────────────┘
```

---

## Unified Concepts Synthesized

| Component | Origin | Description |
| :--- | :--- | :--- |
| **Model Inference & Prompting** | v01–v03 | Structured chat protocol with Ollama Cloud API. |
| **Goal Planning** | v04 | Pre-execution decomposition into ordered strategy steps. |
| **Pluggable Tool Registry** | v05 | Actuators with schema generation and dynamic registration. |
| **Memory Engine** | v06 | Short-term conversation buffer + persistent long-term storage (`agent_memory.json`). |
| **Human Approval & Safety** | v07 | Risk-based guardrails intercepting destructive file/system actions. |
| **Reflection & Evaluation** | v08 | Autonomous critique rubric (1-10) with self-correction retry loops. |
| **Specialist Blueprints** | v10 | Ready-to-use domain personas (CodeCraft, Scholar, Pythagoras, Sentinel). |
| **Multi-Step Coordination** | v11 | Step-by-step observation and synthesis loop. |

---

## File Structure

| File | Description |
| :--- | :--- |
| `builder.py` | Fluent `AgentBuilder` API & `NaturalLanguageAgentBuilder` meta-agent. |
| `agent.py` | `PersonalAgent` runtime orchestrating reasoning, planning, tools, safety, and reflection. |
| `tools.py` | Extensible `ToolRegistry`, tool models, file manipulation, and safe AST math. |
| `memory.py` | `ConversationBuffer` and file-backed `PersistentMemoryStore`. |
| `safety.py` | `SafetyController` and policy management (`PERMISSIVE`, `MODERATE`, `STRICT`). |
| `reflection.py` | `ReflectionEngine` rubric grader and iterative refinement loops. |
| `presets.py` | Turnkey blueprints for Coding, Research, Math Tutor, and Sentinel File agents. |
| `main.py` | Interactive Builder Studio CLI. |

---

## Quickstart & Usage

### 1. Launch the Interactive Studio
```powershell
# Navigate to version 12 directory
cd v12_personal_agent_builder

# Launch the interactive Studio CLI
python main.py
```

### 2. Programmatic Usage (Fluent Builder Pattern)
```python
from builder import AgentBuilder
from safety import SafetyPolicy

# Build a custom assistant in 6 lines of code!
agent = (
    AgentBuilder()
    .with_name("DocWriter")
    .with_goal("Generate and format technical documentation files.")
    .with_file_tools()
    .with_memory("docs_memory.json")
    .with_safety(SafetyPolicy.MODERATE)
    .with_planning(True)
    .with_reflection(True)
    .with_credentials(api_key="YOUR_KEY")
    .build()
)

# Run a task
response = agent.run("Create a quick reference guide in docs/cheatsheet.md")
print(response)
```

### 3. Natural Language Agent Construction
Inside the interactive CLI, select Option 1 and type:
> *"Build a coding agent with file access and human approval."*

The meta-builder will:
1. Detect developer intent.
2. Configure `CodeCraft` persona.
3. Attach file system actuators.
4. Enable Moderate Human-in-the-Loop safety guardrails.
5. Launch an immediate interactive session!
