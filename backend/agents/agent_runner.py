
from pathlib import Path

from agents.planner import AgentPlanner
from tools.tool_executor import ToolExecutor


class AgentRunner:
    """Connect the Agent Planner to the approved Tool Executor."""

    def __init__(self):
        self.planner = AgentPlanner()
        self.executor = ToolExecutor()

    def run(self, user_request, target_file=None):
        """Create a plan and perform a basic, safe tool action."""

        plan = self.planner.create_plan(
            user_request=user_request,
            target_file=target_file,
        )

        if plan["status"] != "success":
            return plan

        task_type = plan["task_type"]
        request = user_request.lower()

        # Choose a read-only tool based on the user's request.
        if any(word in request for word in ("list files", "show files", "project files")):
            tool_result = self.executor.execute("list_files")

        elif any(word in request for word in ("read", "show code", "open file")):
            if not target_file:
                return {
                    "status": "error",
                    "message": "Please provide a target file to read.",
                    "plan": plan,
                }

            tool_result = self.executor.execute(
                "read_file",
                file_path=target_file,
            )

        else:
            return {
                "status": "planned",
                "message": (
                    "The task was planned, but no automatic tool "
                    "action was selected."
                ),
                "plan": plan,
                "execution_started": False,
            }

        return {
            "status": "success",
            "task_type": task_type,
            "plan": plan,
            "tool_result": tool_result,
            "execution_started": True,
        }


if __name__ == "__main__":
    runner = AgentRunner()

    result = runner.run(
        user_request="List project files"
    )

    print("Agent Runner Result:")
    print(result)