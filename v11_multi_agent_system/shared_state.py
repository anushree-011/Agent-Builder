"""
==============================================================================
V11 - MULTI-AGENT SYSTEM: SHARED STATE MODULE
==============================================================================
Concept & Architecture:
In a multi-agent system, specialist agents must collaborate and share data.
The "Shared State" pattern (often termed the Blackboard Architecture) provides
a central shared memory store that:
1. Retains the original user objective.
2. Chronologically records the output of every agent step.
3. Provides contextual history so downstream agents (e.g. Memory Agent or Summary)
   know what upstream agents (e.g. File Agent or Calculator Agent) did.
4. Tracks workflow progress and lists completed agents.
==============================================================================
"""


class SharedState:
    """
    Central blackboard and state container shared across all collaborating agents.
    """

    def __init__(self, task):
        """
        Initializes the shared state object with the primary user task.

        Parameters:
        -----------
        task : str
            The initial high-level user request initiating the workflow.
        """
        # Store original task description
        self.task = task

        # List of result dictionaries: [{"agent": "...", "result": "..."}, ...]
        self.results = []

        # List of agent names that have completed their steps
        self.completed_agents = []

        # Tracks the zero-based index of the current execution step
        self.current_step = 0

    # ==========================================================================
    # SECTION 1: STATE MUTATION METHODS
    # ==========================================================================

    def add_result(self, agent_name, result):
        """
        Appends the execution result of a specialist agent to the shared state.

        Parameters:
        -----------
        agent_name : str
            The identifier of the agent that produced the result.
        result : any
            The output string or structured data returned by the agent.
        """
        # Append result record mapping agent to its output
        self.results.append({
            "agent": agent_name,
            "result": result
        })

        # Track that this agent has successfully contributed to the state
        self.completed_agents.append(agent_name)

    # ==========================================================================
    # SECTION 2: STATE ACCESS METHODS
    # ==========================================================================

    def get_results(self):
        """
        Retrieves the complete list of accumulated agent outputs.

        Returns:
        --------
        list of dict : All recorded results so far.
        """
        return self.results

    # ==========================================================================
    # SECTION 3: VISUALIZATION & MONITORING
    # ==========================================================================

    def display(self):
        """
        Prints a formatted console visualization of the shared state blackboard.
        """
        print()
        print("=" * 60)
        print("SHARED STATE BLACKBOARD")
        print("=" * 60)

        # Print original objective
        print()
        print("Original Task:")
        print(self.task)

        # Print list of agents that have finished tasks
        print()
        print("Completed Agents:")
        if not self.completed_agents:
            print("None")
        else:
            for agent in self.completed_agents:
                print(f"- {agent}")

        # Print full history of outputs
        print()
        print("Accumulated Results:")
        if not self.results:
            print("None")
        else:
            for item in self.results:
                print()
                print(f"Agent:  {item['agent']}")
                print(f"Result: {item['result']}")