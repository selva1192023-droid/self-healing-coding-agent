
from pathlib import Path

from tools.file_tools import (
    list_files,
    read_file,
    write_file,
)


class ToolExecutor:
    """Select and execute approved, basic file tools."""

    def __init__(self, backend_path=None):
        self.backend_path = (
            Path(backend_path).resolve()
            if backend_path
            else Path(__file__).resolve().parent.parent
        )
        self.workspace_path = self.backend_path / "workspace"
        self.workspace_path.mkdir(exist_ok=True)

    def execute(self, tool_name, **arguments):
        """Run one of the approved file tools."""

        if tool_name == "list_files":
            return list_files(self.backend_path)

        if tool_name == "read_file":
            file_path = arguments.get("file_path", "")
            return read_file(self.backend_path, file_path)

        if tool_name == "write_file":
            file_path = arguments.get("file_path", "")
            content = arguments.get("content", "")

            if not file_path:
                return "Error: A file path is required."

            if not isinstance(content, str):
                return "Error: File content must be text."

            return write_file(
                self.workspace_path,
                file_path,
                content,
            )

        return f"Error: Unknown or unauthorized tool: {tool_name}"


if __name__ == "__main__":
    executor = ToolExecutor()

    print("Available tool test:")
    print(executor.execute("list_files"))

    print("\nRead-file tool test:")
    print(executor.execute("read_file", file_path="app/main.py"))

    print("\nTool executor is ready.")