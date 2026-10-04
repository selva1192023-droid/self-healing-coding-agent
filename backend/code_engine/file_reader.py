
from pathlib import Path
from typing import Any


IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
}

SENSITIVE_FILES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}

MAX_FILE_SIZE = 1_000_000  # 1 MB


def read_project_file(project_path: str, file_path: str) -> dict[str, Any]:
    """
    Read a text file located inside the project directory.

    Rejects paths outside the project, sensitive files,
    ignored directories, symlinks, and oversized files.
    """
    root = Path(project_path).expanduser().resolve()
    requested = Path(file_path)

    if not root.exists() or not root.is_dir():
        return {
            "status": "error",
            "message": "Project directory does not exist.",
        }

    if requested.is_absolute():
        target = requested
    else:
        target = root / requested

    # Reject symlinks in the requested path before resolving.
    try:
        relative = target.relative_to(root)
    except ValueError:
        return {
            "status": "error",
            "message": "File path must be inside the project directory.",
        }

    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return {
                "status": "error",
                "message": "Symbolic links are not allowed.",
            }

    target = target.resolve()

    try:
        target.relative_to(root)
    except ValueError:
        return {
            "status": "error",
            "message": "File path resolves outside the project directory.",
        }

    if not target.is_file():
        return {
            "status": "error",
            "message": "Requested path is not a file.",
        }

    if any(part in IGNORED_DIRS for part in relative.parts):
        return {
            "status": "error",
            "message": "Files in ignored directories cannot be read.",
        }

    if target.name.lower() in SENSITIVE_FILES:
        return {
            "status": "error",
            "message": "Reading sensitive files is not allowed.",
        }

    if target.name.lower().startswith(".env."):
        return {
            "status": "error",
            "message": "Reading environment files is not allowed.",
        }

    try:
        size = target.stat().st_size
        if size > MAX_FILE_SIZE:
            return {
                "status": "error",
                "message": "File exceeds the 1 MB size limit.",
            }

        content = target.read_text(encoding="utf-8")

        return {
            "status": "success",
            "file_path": str(relative),
            "size_bytes": size,
            "content": content,
        }

    except UnicodeDecodeError:
        return {
            "status": "error",
            "message": "File is not valid UTF-8 text.",
        }
    except PermissionError:
        return {
            "status": "error",
            "message": "Permission denied while reading the file.",
        }
    except OSError as exc:
        return {
            "status": "error",
            "message": f"Could not read file: {exc}",
        }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 3:
        print(
            "Usage: python -m code_engine.file_reader "
            "<project_directory> <relative_file_path>"
        )
        raise SystemExit(1)

    result = read_project_file(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))