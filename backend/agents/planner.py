
import re
from typing import Any


class AgentPlanner:
    """Classifies coding requests and creates an execution plan."""

    TASK_KEYWORDS = {
        "repair": [
            "fix",
            "repair",
            "correct",
            "resolve",
            "solve this bug",
            "fix this bug",
            "apply the fix",
            "modify the code",
            "change the code",
        ],
        "debug": [
            "debug",
            "bug",
            "find the bug",
            "identify the bug",
            "detect the bug",
            "find bugs",
            "identify bugs",
            "detect bugs",
            "find the error",
            "identify the error",
            "detect errors",
            "find errors",
            "what is wrong",
            "what went wrong",
            "why is this failing",
            "why does this fail",
            "error",
            "exception",
            "traceback",
            "not working",
            "fails",
            "failure",
        ],
        "generate": [
            "create",
            "generate",
            "write",
            "build",
            "implement",
            "develop",
        ],
        "explain": [
            "explain",
            "describe",
            "how does",
            "what does",
            "understand",
        ],
    }

    def classify_task(self, user_request: str) -> str:
        """Identify the likely task type from the user's request."""

        text = user_request.lower().strip()

        # Prioritize explicit repair requests over other task types.
        for task_type in ("repair", "debug", "generate", "explain"):
            for keyword in self.TASK_KEYWORDS[task_type]:
                pattern = (
                    r"(?<!\w)"
                    + re.escape(keyword)
                    + r"(?!\w)"
                )

                if re.search(pattern, text):
                    return task_type

        return "general"

    def create_plan(
        self,
        user_request: str,
        target_file: str | None = None,
    ) -> dict[str, Any]:
        """Create a structured plan for the coding agent."""

        if not user_request or not user_request.strip():
            return {
                "status": "error",
                "message": "The user request cannot be empty.",
            }

        task_type = self.classify_task(user_request)

        plans = {
            "generate": [
                "Understand the requested functionality.",
                "Review relevant project files and existing code.",
                "Design a solution consistent with the project structure.",
                "Generate the required code.",
                "Review the code for correctness and safety.",
                "Prepare validation steps.",
            ],
            "debug": [
                "Understand the reported error and expected behavior.",
                "Inspect the relevant source files and error details.",
                "Identify the likely cause of the error.",
                "Propose a targeted correction.",
                "Prepare tests to verify the correction.",
                "Summarize the diagnosis and proposed fix.",
            ],
            "repair": [
                "Understand the requested repair and expected behavior.",
                "Inspect the relevant source files.",
                "Identify the defect and affected components.",
                "Develop a minimal, targeted code correction.",
                "Prepare tests for the repaired behavior.",
                "Summarize the proposed changes and validation.",
            ],
            "explain": [
                "Identify the code or concept the user wants explained.",
                "Gather relevant project context, if available.",
                "Analyze the code structure and behavior.",
                "Prepare a clear, step-by-step explanation.",
                "Include examples or improvement suggestions if useful.",
            ],
            "general": [
                "Analyze the user's request.",
                "Determine the relevant project context and requirements.",
                "Identify the appropriate coding-agent workflow.",
                "Prepare a response or implementation plan.",
                "Review the result for completeness.",
            ],
        }

        steps = plans[task_type]

        return {
            "status": "success",
            "task_type": task_type,
            "user_request": user_request.strip(),
            "target_file": target_file,
            "total_steps": len(steps),
            "steps": [
                {
                    "step": index,
                    "description": description,
                    "status": "pending",
                }
                for index, description in enumerate(steps, start=1)
            ],
            "execution_started": False,
            "files_modified": [],
        }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Plan a coding-agent task."
    )
    parser.add_argument(
        "request",
        nargs="+",
        help="Coding task to plan.",
    )
    parser.add_argument(
        "--file",
        dest="target_file",
        help="Optional relative target file.",
    )

    args = parser.parse_args()

    planner = AgentPlanner()
    result = planner.create_plan(
        user_request=" ".join(args.request),
        target_file=args.target_file,
    )

    print(json.dumps(result, indent=2))
