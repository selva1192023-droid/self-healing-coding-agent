
from pathlib import Path


def list_files(project_path):
    """List files and folders in a project directory."""
    folder = Path(project_path).resolve()

    if not folder.exists():
        return ["Project folder not found"]

    if not folder.is_dir():
        return ["The given path is not a directory"]

    return sorted(item.name for item in folder.iterdir())


def read_file(project_path, file_path):
    """Safely read a file inside the project directory."""
    root = Path(project_path).resolve()
    target = (root / file_path).resolve()

    if not target.is_relative_to(root):
        return "Error: Access outside the project is not allowed."

    if not target.exists():
        return "Error: File not found."

    if not target.is_file():
        return "Error: The path is not a file."

    if target.name.lower() in {
        ".env", "secrets.json", "credentials.json"
    }:
        return "Error: Reading sensitive files is not allowed."

    if target.stat().st_size > 1_000_000:
        return "Error: File is too large to read."

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "Error: File is not a readable UTF-8 text file."
    except OSError:
        return "Error: Unable to read the file."


def write_file(workspace_path, file_path, content):
    """Create a new file inside the designated workspace."""
    root = Path(workspace_path).resolve()
    target = (root / file_path).resolve()

    if not target.is_relative_to(root):
        return "Error: Writing outside the workspace is not allowed."

    if target.exists():
        return "Error: File already exists. No changes made."

    if not target.parent.is_dir():
        return "Error: Destination folder does not exist."

    if not target.parent.is_relative_to(root):
        return "Error: Invalid destination folder."

    try:
        target.write_text(content, encoding="utf-8")
        return f"Success: Created {target.relative_to(root)}"
    except OSError:
        return "Error: Unable to create the file."


if __name__ == "__main__":
    backend_path = Path(__file__).resolve().parent.parent
    workspace_path = backend_path / "workspace"

    print("Project files:")
    for file in list_files(backend_path):
        print(file)

    print("\nReading app/main.py:")
    print(read_file(backend_path, "app/main.py"))

    print("\nTesting file creation:")
    result = write_file(
        workspace_path,
        "hello.py",
        'print("Hello from the coding agent!")'
    )
    print(result)