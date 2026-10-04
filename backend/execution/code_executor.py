
import subprocess
import sys
from pathlib import Path


class CodeExecutor:
    """Execute Python files from the agent's workspace."""

    def __init__(self):
        self.backend_path = Path(__file__).resolve().parent.parent
        self.workspace_path = (
            self.backend_path / "workspace"
        ).resolve()

        self.workspace_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def execute_python(self, file_path, timeout=10):
        """Run a Python file and capture its output and errors."""

        target = (
            self.workspace_path / file_path
        ).resolve()

        # Prevent execution outside the workspace
        if not target.is_relative_to(self.workspace_path):
            return {
                "status": "error",
                "message": "Execution outside workspace is not allowed.",
            }

        # Only allow Python files
        if target.suffix.lower() != ".py":
            return {
                "status": "error",
                "message": "Only Python files can be executed.",
            }

        if not target.is_file():
            return {
                "status": "error",
                "message": "Python file not found.",
            }

        try:
            result = subprocess.run(
                [sys.executable, str(target)],
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            return {
                "status": (
                    "success" if result.returncode == 0
                    else "error"
                ),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Execution timed out after {timeout} seconds.",
            }

        except OSError as exc:
            return {
                "status": "error",
                "message": f"Execution failed: {exc}",
            }


if __name__ == "__main__":
    executor = CodeExecutor()

    result = executor.execute_python("hello.py")

    print("Code Execution Result:")
    print("-" * 30)
    print(result)