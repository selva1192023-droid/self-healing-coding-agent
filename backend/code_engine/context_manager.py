
import argparse
import ast
import json
import logging
import os
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

MAX_SOURCE_FILES = 12
MAX_FILE_CHARS = 8000
MAX_TOTAL_SOURCE_CHARS = 60000
MAX_PROJECT_FILES = 5000
MAX_PROJECT_DIRS = 20000

IGNORED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__",
    "node_modules", ".idea", ".vscode", "dist", "build",
    ".next", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}

SENSITIVE_NAMES = {
    ".env", ".env.local", ".env.production",
    ".env.development", "id_rsa", "id_ed25519",
    "credentials", "secrets.json", "secrets.yaml", "secrets.yml",
}

SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}

SOURCE_PRIORITY = [
    "app/api/coding.py",
    "app/main.py",
    "app/services/llm_service.py",
    "agents/agent_runner.py",
    "agents/planner.py",
    "code_engine/context_manager.py",
    "code_engine/project_scanner.py",
    "code_engine/file_reader.py",
    "code_engine/code_parser.py",
    "execution/code_executor.py",
    "repair/repair_engine.py",
    "repair/self_healing_agent.py",
    "testing/error_detector.py",
    "tools/tool_executor.py",
    "tools/file_tools.py",
]

TASK_MODULES = {
    "explain": [
        "app/api/coding.py",
        "app/main.py",
        "app/services/llm_service.py",
        "agents/agent_runner.py",
        "agents/planner.py",
        "execution/code_executor.py",
        "repair/repair_engine.py",
        "repair/self_healing_agent.py",
        "testing/error_detector.py",
        "tools/tool_executor.py",
        "tools/file_tools.py",
        "code_engine/file_reader.py",
        "code_engine/context_manager.py",
        "code_engine/project_scanner.py",
        "code_engine/code_parser.py",
    ],
    "debug": [
        "app/api/coding.py",
        "app/services/llm_service.py",
        "agents/agent_runner.py",
        "agents/planner.py",
        "execution/code_executor.py",
        "testing/error_detector.py",
        "repair/repair_engine.py",
        "repair/self_healing_agent.py",
        "tools/tool_executor.py",
        "tools/file_tools.py",
        "code_engine/file_reader.py",
        "code_engine/code_parser.py",
    ],
    "repair": [
        "repair/self_healing_agent.py",
        "repair/repair_engine.py",
        "testing/error_detector.py",
        "execution/code_executor.py",
        "tools/tool_executor.py",
        "tools/file_tools.py",
        "agents/agent_runner.py",
        "agents/planner.py",
        "app/api/coding.py",
        "app/services/llm_service.py",
        "code_engine/file_reader.py",
        "code_engine/code_parser.py",
    ],
    "generate": [
        "app/api/coding.py",
        "app/services/llm_service.py",
        "agents/planner.py",
        "agents/agent_runner.py",
        "tools/tool_executor.py",
        "tools/file_tools.py",
        "code_engine/context_manager.py",
        "code_engine/file_reader.py",
        "code_engine/code_parser.py",
    ],
    "test": [
        "testing/error_detector.py",
        "execution/code_executor.py",
        "repair/repair_engine.py",
        "repair/self_healing_agent.py",
        "agents/agent_runner.py",
        "agents/planner.py",
        "tools/tool_executor.py",
        "app/api/coding.py",
    ],
}


class ContextManager:
    """Build bounded, task-aware context from a project directory."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()

    def _is_inside_project(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.project_root)
            return True
        except (ValueError, OSError, RuntimeError):
            return False

    @staticmethod
    def _is_sensitive_file(path: Path) -> bool:
        name = path.name.lower()

        if name in SENSITIVE_NAMES:
            return True

        if name.startswith(".env") and name != ".env.example":
            return True

        return path.suffix.lower() in SENSITIVE_SUFFIXES

    def _validate_target(self, target_file: str | None) -> Path | None:
        if not target_file:
            return None

        supplied = Path(target_file)

        if supplied.is_absolute() or ".." in supplied.parts:
            raise ValueError("Target file must be a safe relative path.")

        target = (self.project_root / supplied).resolve()

        if not self._is_inside_project(target):
            raise ValueError("Target file must be inside the project.")

        if target.suffix.lower() != ".py":
            raise ValueError("Target file must be a Python (.py) file.")

        if not target.exists():
            raise ValueError("Target file does not exist.")

        if target.is_symlink() or not target.is_file():
            raise ValueError("Target must be a regular, non-symlink file.")

        if self._is_sensitive_file(target):
            raise ValueError("Target file may contain sensitive information.")

        return target

    def _scan_project(self) -> tuple[list[dict[str, str]], bool]:
        """Create a bounded inventory, skipping symlinks and sensitive files."""
        inventory: list[dict[str, str]] = []
        visited_dirs = 0
        truncated = False

        for root, dir_names, file_names in os.walk(
            self.project_root,
            topdown=True,
            followlinks=False,
        ):
            root_path = Path(root)

            dir_names[:] = [
                name for name in dir_names
                if name not in IGNORED_DIRS
                and not (root_path / name).is_symlink()
            ]

            visited_dirs += 1
            if visited_dirs > MAX_PROJECT_DIRS:
                truncated = True
                break

            for name in file_names:
                path = root_path / name

                try:
                    if path.is_symlink() or not path.is_file():
                        continue
                    if self._is_sensitive_file(path):
                        continue

                    relative = path.relative_to(
                        self.project_root
                    ).as_posix()

                    inventory.append({
                        "name": path.name,
                        "path": relative,
                        "extension": path.suffix.lower(),
                    })

                    if len(inventory) >= MAX_PROJECT_FILES:
                        truncated = True
                        break

                except (OSError, ValueError, RuntimeError):
                    logger.warning("Skipped inaccessible project entry.")
                    continue

            if truncated:
                break

        return inventory, truncated

    @staticmethod
    def _normalize_candidate(candidate: Any) -> str | None:
        if isinstance(candidate, dict):
            candidate = candidate.get("path")

        if not isinstance(candidate, str) or not candidate.strip():
            return None

        return candidate.replace("\\", "/").lstrip("./")

    def _select_source_files(
        self,
        candidates: list[Any],
        target_file: str | None = None,
        task_type: str | None = None,
    ) -> list[str]:
        """Select task-relevant files, then fill remaining slots by priority."""
        available = {
            normalized
            for candidate in candidates
            if (normalized := self._normalize_candidate(candidate))
        }

        target_normalized = (
            target_file.replace("\\", "/").lstrip("./")
            if target_file else None
        )
        if target_normalized:
            available.discard(target_normalized)

        task_key = str(task_type or "").strip().lower()
        preferred = TASK_MODULES.get(task_key, SOURCE_PRIORITY)

        selected: list[str] = []

        for path in preferred:
            if path in available and path not in selected:
                selected.append(path)
                if len(selected) >= MAX_SOURCE_FILES:
                    return selected

        for path in SOURCE_PRIORITY:
            if path in available and path not in selected:
                selected.append(path)
                if len(selected) >= MAX_SOURCE_FILES:
                    return selected

        for path in sorted(available):
            if path not in selected:
                selected.append(path)
                if len(selected) >= MAX_SOURCE_FILES:
                    break

        return selected

    def _read_file(self, relative_path: str) -> str:
        """Read a bounded, validated Python file from the project."""
        candidate = (self.project_root / relative_path).resolve()

        if not self._is_inside_project(candidate):
            raise ValueError("Source file is outside the project.")

        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError("Source file is not a regular file.")

        if self._is_sensitive_file(candidate):
            raise ValueError("Source file is excluded as potentially sensitive.")

        if candidate.suffix.lower() != ".py":
            raise ValueError("Only Python source files are included.")

        with candidate.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(MAX_FILE_CHARS + 1)[:MAX_FILE_CHARS]

    def _read_additional_sources(
        self,
        files: list[Any],
        target_file: str | None = None,
        task_type: str | None = None,
    ) -> tuple[dict[str, str], list[str]]:
        selected = self._select_source_files(
            files,
            target_file=target_file,
            task_type=task_type,
        )

        source_files: dict[str, str] = {}
        errors: list[str] = []
        total_chars = 0

        for relative_path in selected:
            if total_chars >= MAX_TOTAL_SOURCE_CHARS:
                break

            try:
                content = self._read_file(relative_path)
                remaining = MAX_TOTAL_SOURCE_CHARS - total_chars
                content = content[:remaining]

                source_files[relative_path] = content
                total_chars += len(content)

            except (OSError, ValueError, UnicodeError) as exc:
                errors.append(f"{relative_path}: {exc}")
                logger.warning("Could not read %s: %s", relative_path, exc)

        return source_files, errors

    @staticmethod
    def _parse_python_source(source: str) -> dict[str, Any]:
        """Return a basic AST summary for a Python source string."""
        try:
            tree = ast.parse(source)
            imports: set[str] = set()
            functions: set[str] = set()
            classes: set[str] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.add(node.module or "")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.add(node.name)

            return {
                "status": "success",
                "imports": sorted(imports),
                "functions": sorted(functions),
                "classes": sorted(classes),
            }

        except SyntaxError as exc:
            return {
                "status": "error",
                "error": f"Syntax error at line {exc.lineno}: {exc.msg}",
                "imports": [],
                "functions": [],
                "classes": [],
            }

    def build_context(
        self,
        target_file: str | None = None,
        task_type: str | None = None,
    ) -> dict[str, Any]:
        """Build inventory, target details, and relevant source context."""
        try:
            if not self.project_root.exists():
                return {
                    "status": "error",
                    "error": "Project root does not exist.",
                    "project_root": str(self.project_root),
                }

            if not self.project_root.is_dir():
                return {
                    "status": "error",
                    "error": "Project root is not a directory.",
                    "project_root": str(self.project_root),
                }

            validated_target = self._validate_target(target_file)
            inventory, truncated = self._scan_project()

            target_relative = (
                validated_target.relative_to(
                    self.project_root
                ).as_posix()
                if validated_target else None
            )

            target_content = None
            target_ast = None

            if validated_target:
                target_content = self._read_file(target_relative)
                target_ast = self._parse_python_source(target_content)

            source_files, source_file_errors = self._read_additional_sources(
                inventory,
                target_file=target_relative,
                task_type=task_type,
            )

            return {
                "status": "success",
                "project_root": str(self.project_root),
                "total_files": len(inventory),
                "truncated": truncated,
                "task_type": task_type,
                "target_file": target_relative,
                "target_content": target_content,
                "target_ast": target_ast,
                "file_inventory": inventory,
                "source_files": source_files,
                "source_file_errors": source_file_errors,
            }

        except (OSError, ValueError, RuntimeError) as exc:
            logger.exception("Failed to build project context")
            return {
                "status": "error",
                "error": str(exc),
                "project_root": str(self.project_root),
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build bounded project source context."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root directory.",
    )
    parser.add_argument(
        "--file",
        dest="target_file",
        default=None,
        help="Optional project-relative Python target file.",
    )
    parser.add_argument(
        "--task",
        dest="task_type",
        default=None,
        help="Optional task type for source selection.",
    )

    args = parser.parse_args()
    manager = ContextManager(args.project_root)
    result = manager.build_context(
        target_file=args.target_file,
        task_type=args.task_type,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
