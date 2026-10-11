"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: CORE AGENT RUNTIME
==============================================================================
Concept & Architecture:
This module implements `PersonalAgent`, the central execution engine of the
v12 Personal Agent Builder framework. It represents the culmination of all
prior versions (v01-v11), combining:
- Model inference & prompt engineering (v01-v03)
- Goal-directed planning (v04)
- Reusable tool execution (v05)
- Short-term & persistent memory (v06)
- Safety guardrails & human approval (v07)
- Reflection & self-evaluation (v08)
- Domain specialist capabilities (v10)
- Multi-step coordination & state tracking (v11)

Agent Loop Lifecycle:
1. Receive user task.
2. If planning enabled: Generate explicit step-by-step strategy.
3. Formulate prompt injecting persona, tools schema, and working memory.
4. Call LLM to produce thoughts and tool call or final text.
5. If tool call generated:
   - Check Safety Controller (HITL verification if risk warrants).
   - If approved: Execute tool and capture observation.
   - If rejected: Return safety denial observation to LLM.
   - Feed observation back to model for synthesis.
6. If reflection enabled:
   - Grade candidate answer against rubric.
   - Refine if score is below acceptance threshold.
7. Commit interaction to memory and return answer.
==============================================================================
"""

import json
import requests
from typing import Dict, Any, Optional, List

from tools import ToolRegistry
from memory import ConversationBuffer, PersistentMemoryStore
from safety import SafetyController, SafetyPolicy
from reflection import ReflectionEngine


class PersonalAgent:
    """
    Fully configurable Agentic AI runtime combining reasoning, tools, memory,
    planning, safety guardrails, and self-reflection.
    """

    def __init__(
        self,
        name: str,
        goal: str,
        system_persona: Optional[str] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory_store: Optional[PersistentMemoryStore] = None,
        safety_controller: Optional[SafetyController] = None,
        enable_planning: bool = False,
        enable_reflection: bool = False,
        api_key: Optional[str] = None,
        base_url: str = "https://ollama.com/api",
        model_name: str = "gemma4:31b"
    ):
        """
        Parameters:
        -----------
        name : str
            Unique name of this agent persona.
        goal : str
            Core overarching objective of the agent.
        system_persona : Optional[str]
            Custom instructions shaping style, tone, and domain boundaries.
        tool_registry : Optional[ToolRegistry]
            Registry containing the actuators available to this agent.
        memory_store : Optional[PersistentMemoryStore]
            Long-term memory persistence backend.
        safety_controller : Optional[SafetyController]
            Human-in-the-loop safety validator.
        enable_planning : bool
            Whether to formulate explicit multi-step plans before tool usage.
        enable_reflection : bool
            Whether to run iterative self-evaluation & refinement on outputs.
        api_key : Optional[str]
            Bearer API token for Ollama Cloud inference.
        base_url : str
            Ollama endpoint base URL.
        model_name : str
            LLM model identifier.
        """
        self.name = name
        self.goal = goal
        self.system_persona = system_persona or (
            f"You are {name}, an autonomous agent specialized in achieving: {goal}."
        )

        self.tools = tool_registry or ToolRegistry()
        self.memory_store = memory_store
        self.safety = safety_controller or SafetyController(policy=SafetyPolicy.MODERATE)

        self.enable_planning = enable_planning
        self.enable_reflection = enable_reflection

        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

        # Short-term working conversation buffer
        self.buffer = ConversationBuffer(max_turns=12)

        # Reflection engine (lazily initialized if enabled)
        self.reflection = (
            ReflectionEngine(llm_caller=self._call_llm)
            if self.enable_reflection
            else None
        )

    # ==========================================================================
    # SECTION 1: LLM INFERENCE
    # ==========================================================================

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Dispatches HTTP POST request to Ollama Cloud chat endpoint.

        Parameters:
        -----------
        messages : list of dict
            Chat message list [{"role": "system"|"user", "content": "..."}].

        Returns:
        --------
        str : The response content string.
        """
        url = f"{self.base_url}/chat"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    # ==========================================================================
    # SECTION 2: PROMPT ASSEMBLY
    # ==========================================================================

    def _build_system_prompt(self) -> str:
        """
        Synthesizes the comprehensive system prompt exposing persona, tools,
        and JSON execution schema.
        """
        tools_catalog = self.tools.get_prompt_catalog()

        prompt = f"""
{self.system_persona}

Primary Goal:
{self.goal}

Available Tools:
{tools_catalog}

Execution Instructions:
You can either invoke a tool to gather data/take an action, or provide a direct response.

If you choose to use a tool, return ONLY a JSON object:
{{
    "thought": "<brief reasoning for why this tool is selected>",
    "tool": "<tool_name>",
    "arguments": {{<key>: <value>}}
}}

If no tool is needed and you are ready to answer the user:
{{
    "thought": "<reasoning for final response>",
    "response": "<your final response text>"
}}

CRITICAL RULES:
1. Return ONLY valid JSON.
2. Do NOT wrap JSON in markdown blocks like ```json.
3. Only use tools listed in the Available Tools catalog.
"""
        return prompt.strip()

    # ==========================================================================
    # SECTION 3: JSON CLEANING & PARSING
    # ==========================================================================

    def _parse_agent_response(self, raw_text: str) -> Dict[str, Any]:
        """Cleans and extracts JSON payload from model response."""
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: Treat raw text as direct response
            return {
                "thought": "Direct text fallback",
                "response": raw_text
            }

    # ==========================================================================
    # SECTION 4: AGENT EXECUTION LOOP
    # ==========================================================================

    def run(self, user_prompt: str) -> str:
        """
        Executes the full agentic lifecycle for a user task.

        Parameters:
        -----------
        user_prompt : str
            The input task or query from the user.

        Returns:
        --------
        str : The final verified output of the agent.
        """
        print(f"\n[{self.name}] Initiating task: '{user_prompt}'")

        # Optional Step: Explicit Planning Phase
        plan_context = ""
        if self.enable_planning:
            print(f"[{self.name}] Formulating execution strategy...")
            planning_messages = [
                {"role": "system", "content": "You are a strategic planner. Break the user task into 2-4 ordered bullet points."},
                {"role": "user", "content": f"Task: {user_prompt}"}
            ]
            plan = self._call_llm(planning_messages)
            plan_context = f"\nExecution Strategy:\n{plan}\n"
            print(f"[{self.name}] Plan formulated:\n{plan}")

        # Assemble conversation messages
        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        # Inject existing buffered working memory
        for msg in self.buffer.get_messages():
            messages.append(msg)

        # Inject current prompt with any planning context
        current_user_content = f"{user_prompt}\n{plan_context}".strip()
        messages.append({"role": "user", "content": current_user_content})

        max_tool_steps = 5
        current_step = 0
        final_answer = ""

        # ReAct / Tool Execution Loop
        while current_step < max_tool_steps:
            current_step += 1
            raw_response = self._call_llm(messages)
            parsed = self._parse_agent_response(raw_response)

            thought = parsed.get("thought", "")
            if thought:
                print(f"[{self.name} Thought]: {thought}")

            # Check if agent requested a tool
            tool_name = parsed.get("tool")
            if tool_name and tool_name.lower() != "none":
                arguments = parsed.get("arguments", {})
                tool = self.tools.get(tool_name)

                if not tool:
                    observation = f"Tool '{tool_name}' not found."
                else:
                    # Safety Guardrail Verification
                    approved, reason = self.safety.check_approval(tool, arguments)
                    if approved:
                        print(f"[{self.name} Action]: Executing {tool_name} with {arguments}")
                        observation = tool.execute(**arguments)
                    else:
                        print(f"[{self.name} Safety Block]: {reason}")
                        observation = f"Execution DENIED by safety guardrail: {reason}"

                print(f"[{self.name} Observation]: {observation}")

                # Append tool turn to messages for next cycle
                messages.append({"role": "assistant", "content": raw_response})
                messages.append({
                    "role": "user",
                    "content": f"Tool '{tool_name}' Output / Observation:\n{observation}\nNow provide the final response or choose next step."
                })
            else:
                # Direct answer returned
                final_answer = parsed.get("response", raw_response)
                break

        if not final_answer:
            final_answer = "Agent completed execution but did not formulate a final response."

        # Optional Step: Reflection & Self-Evaluation Pass
        if self.enable_reflection and self.reflection:
            print(f"[{self.name}] Performing self-evaluation reflection pass...")
            eval_result = self.reflection.evaluate(user_prompt, final_answer)
            score = eval_result.get("score", 10)
            feedback = eval_result.get("feedback", "")
            print(f"[{self.name} Reflection]: Score {score}/10 | Feedback: {feedback}")

            if not eval_result.get("passed", True):
                print(f"[{self.name}] Score below threshold. Refining output...")
                final_answer = self.reflection.refine(user_prompt, final_answer, eval_result)
                print(f"[{self.name}] Output successfully refined.")

        # Update working conversation buffer
        self.buffer.add_message("user", user_prompt)
        self.buffer.add_message("assistant", final_answer)

        return final_answer
