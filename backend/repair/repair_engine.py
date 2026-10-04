
import ast
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


class RepairEngine:
    """Validate and safely apply proposed Python code repairs."""

    def __init__(self, workspace_path: str | Path):
        self.workspace = Path(workspace_path).resolve()

    def _resolve_target(self, file_path: str | Path) -> Path:
        """Resolve a target file and ensure it stays inside the workspace."""
        target = (self.workspace / file_path).resolve()

        if not target.is_relative_to(self.workspace):
            raise ValueError("Target file is outside the workspace.")

        if target.suffix.lower() != ".py":
            raise ValueError("Only Python files can be repaired.")

        return target

    @staticmethod
    def validate_python(content: str) -> dict[str, Any]:
        """Check Python syntax without executing the code."""
        try:
            ast.parse(content)
            return {
                "status": "success",
                "message": "Python syntax is valid.",
            }
        except SyntaxError as exc:
            return {
                "status": "error",
                "message": exc.msg,
                "line": exc.lineno,
                "column": exc.offset,
            }

    def propose_repair(
        self,
        original_content: str,
        diagnosis: dict[str, Any],
        repaired_content: str,
    ) -> dict[str, Any]:
        """Validate a proposed fix without modifying any files."""
        validation = self.validate_python(repaired_content)

        if validation["status"] != "success":
            return {
                "status": "rejected",
                "message": "The proposed repair contains a syntax error.",
                "validation": validation,
                "diagnosis": diagnosis,
            }

        return {
            "status": "ready",
            "message": "The proposed repair passed Python syntax validation.",
            "original_length": len(original_content),
            "repaired_length": len(repaired_content),
            "diagnosis": diagnosis,
            "repaired_content": repaired_content,
        }

    def apply_repair(
        self,
        file_path: str | Path,
        repaired_content: str,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Back up and apply a valid repair after explicit confirmation."""
        if not confirm:
            return {
                "status": "confirmation_required",
                "message": "Set confirm=True to apply the repair.",
            }

        target = self._resolve_target(file_path)

        if not target.is_file():
            return {
                "status": "error",
                "message": "Target file does not exist.",
            }

        validation = self.validate_python(repaired_content)
        if validation["status"] != "success":
            return {
                "status": "rejected",
                "message": "Repair was not applied because syntax validation failed.",
                "validation": validation,
            }

        try:
            original_content = target.read_text(encoding="utf-8")
            backup_path = target.with_suffix(target.suffix + ".bak")

            # Preserve the original file before changing it.
            shutil.copy2(target, backup_path)

            # Write to a temporary file in the same directory, then replace.
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    newline="",
                    suffix=".tmp",
                    prefix="repair_",
                    dir=target.parent,
                    delete=False,
                ) as temp_file:
                    temp_file.write(repaired_content)
                    temp_path = Path(temp_file.name)

                os.replace(temp_path, target)
                temp_path = None
            finally:
                if temp_path is not None and temp_path.exists():
                    temp_path.unlink()

            return {
                "status": "success",
                "message": "Repair applied successfully.",
                "file": str(target),
                "backup": str(backup_path),
                "original_length": len(original_content),
                "repaired_length": len(repaired_content),
            }

        except (OSError, UnicodeError, ValueError) as exc:
            return {
                "status": "error",
                "message": f"Could not apply repair: {exc}",
            }


if __name__ == "__main__":
    workspace = Path(__file__).resolve().parent.parent / "workspace"
    engine = RepairEngine(workspace)

    original = "def greet():\n    print('Hello'\n"
    diagnosis = {
        "error_type": "SyntaxError",
        "message": "Missing closing parenthesis",
    }
    repaired = "def greet():\n    print('Hello')\n"

    proposal = engine.propose_repair(original, diagnosis, repaired)
    print("Repair proposal:")
    print(proposal)

    print("\nSyntax validation:")
    print(engine.validate_python(repaired))

    print("\nNo files were modified by this test.")