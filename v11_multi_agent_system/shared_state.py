"""
============================================================
V11 - SHARED STATE
============================================================

Shared state allows multiple specialist agents to share
information during one task.

Example:

File Agent:
    Created folder V11_Project

Memory Agent:
    Saved memory about V11_Project

Calculator Agent:
    Calculated 3 specialist agents

All of these results are stored here.
============================================================
"""


class SharedState:
    """
    Stores information shared between agents.
    """

    def __init__(self, task):

        # Original user task
        self.task = task

        # Results returned by agents
        self.results = []

        # Agents that completed their work
        self.completed_agents = []

        # Current execution step
        self.current_step = 0


    # ========================================================
    # ADD RESULT
    # ========================================================

    def add_result(self, agent_name, result):

        self.results.append({
            "agent": agent_name,
            "result": result
        })

        self.completed_agents.append(
            agent_name
        )


    # ========================================================
    # GET PREVIOUS RESULTS
    # ========================================================

    def get_results(self):

        return self.results


    # ========================================================
    # DISPLAY STATE
    # ========================================================

    def display(self):

        print()
        print("=" * 60)
        print("SHARED STATE")
        print("=" * 60)

        print()
        print("Original Task:")
        print(self.task)

        print()
        print("Completed Agents:")

        if not self.completed_agents:

            print("None")

        else:

            for agent in self.completed_agents:

                print(
                    f"- {agent}"
                )

        print()
        print("Results:")

        if not self.results:

            print("None")

        else:

            for item in self.results:

                print()
                print(
                    f"Agent: {item['agent']}"
                )

                print(
                    f"Result: {item['result']}"
                )