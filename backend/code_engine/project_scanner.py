
import os
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
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

IGNORED_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
}

SENSITIVE_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}

MAX_FILES = 5000
MAX_DIRECTORIES = 20000


def _is_sensitive_file(filename: str) -> bool:
    """Return True for common secret and private-key filenames."""
    lowered = filename.lower()

    if lowered in IGNORED_FILES:
        return True

    if lowered.startswith(".env"):
        return True

    if Path(lowered).suffix in SENSITIVE_SUFFIXES:
        return True

    return False


def scan_project(project_path: str) -> dict[str, Any]:
    """
    Scan a project directory and return a limited file inventory.

    Does not read file contents or follow symbolic links.
    Excludes common dependency, cache, and sensitive files.
    """
    root = Path(project_path).expanduser().resolve()

    if not root.exists():
        return {
            "status": "error",
            "message": "Project path does not exist.",
            "files": [],
            "total_files": 0,
        }

    if not root.is_dir():
        return {
            "status": "error",
            "message": "Project path is not a directory.",
            "files": [],
            "total_files": 0,
        }

    files: list[dict[str, str]] = []
    truncated = False
    visited_directories = 0

    try:
        for current_dir, dirs, filenames in os.walk(
            root,
            topdown=True,
            followlinks=False,
            onerror=lambda error: (_ for _ in ()).throw(error),
        ):
            visited_directories += 1

            if visited_directories > MAX_DIRECTORIES:
                truncated = True
                break

            current_path = Path(current_dir)

            # Do not descend into ignored, hidden, or symlinked directories.
            safe_dirs = []

            for name in dirs:
                directory_path = current_path / name

                if name in IGNORED_DIRS or name.startswith("."):
                    continue

                if directory_path.is_symlink():
                    continue

                safe_dirs.append(name)

            dirs[:] = safe_dirs

            for filename in filenames:
                if _is_sensitive_file(filename):
                    continue

                file_path = current_path / filename

                # Exclude symbolic links and non-regular files.
                try:
                    if file_path.is_symlink() or not file_path.is_file():
                        continue

                    relative_path = file_path.relative_to(root)
                except (OSError, ValueError):
                    continue

                files.append({
                    "name": filename,
                    "path": str(relative_path),
                    "extension": file_path.suffix.lower(),
                })

                if len(files) >= MAX_FILES:
                    truncated = True
                    break

            if truncated:
                break

    except (PermissionError, OSError) as exc:
        return {
            "status": "error",
            "message": f"Unable to complete project scan: {exc}",
            "project_path": str(root),
            "total_files": len(files),
            "truncated": truncated,
            "files": files,
        }

    return {
        "status": "success",
        "project_path": str(root),
        "total_files": len(files),
        "truncated": truncated,
        "files": files,
    }


if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    result = scan_project(target)
    print(json.dumps(result, indent=2))