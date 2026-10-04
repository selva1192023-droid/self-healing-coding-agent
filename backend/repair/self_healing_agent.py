from pathlib import Path
from typing import Any

from execution.code_executor import CodeExecutor
from repair.repair_engine import RepairEngine
from testing.error_detector import ErrorDetector


class SelfHealingAgent:
    """Coordinate error detection, repair validation, and re-execution."""

    def __init__(self):
        self.backend_path = Path(__file__).resolve().parent.parent
        self.workspace_path = (
            self.backend_path / "workspace"
        ).resolve()

        self.executor = CodeExecutor()
        self.detector = ErrorDetector()
        self.repair_engine = RepairEngine(self.workspace_path)

    def _validate_target(self, file_path: str) -> tuple[Path | None, dict[str, Any] | None]:
        """Validate that the target is an existing Python file in the workspace."""
        target = (self.workspace_path / file_path).resolve()

        if not target.is_relative_to(self.workspace_path):
            return None, {
                "status": "rejected",
                "message": "Target file is outside the workspace.",
            }

        if target.suffix.lower() != ".py":
            return None, {
                "status": "rejected",
                "message": "Only Python files are supported.",
            }

        if not target.is_file():
            return None, {
                "status": "error",
                "message": "Target Python file does not exist.",
            }

        return target, None

    def diagnose(
        self,
        file_path: str,
        allow_execution: bool = False,
    ) -> dict[str, Any]:
        """Check syntax; execute only when explicitly approved."""
        target, validation_error = self._validate_target(file_path)

        if validation_error:
            return validation_error

        syntax_result = self.detector.detect_syntax_error(target)

        if syntax_result.get("status") == "error":
            return {
                "status": "error",
                "stage": "syntax_check",
                "diagnosis": syntax_result,
            }

        if not allow_execution:
            return {
                "status": "approval_required",
                "stage": "execution",
                "message": (
                    "Syntax check passed. Program execution was skipped. "
                    "Call diagnose(..., allow_execution=True) only after "
                    "reviewing and approving the file."
                ),
                "syntax_check": syntax_result,
            }

        execution_result = self.executor.execute_python(file_path)
        diagnosis = self.detector.analyze_execution_result(
            execution_result
        )

        return {
            "status": diagnosis.get("status", "error"),
            "stage": "execution",
            "diagnosis": diagnosis,
            "execution_result": execution_result,
        }

    def repair_and_verify(
        self,
        file_path: str,
        repaired_content: str,
        confirm: bool = False,
        allow_execution: bool = False,
    ) -> dict[str, Any]:
        """Validate and apply a repair; execute only with explicit approval."""
        target, validation_error = self._validate_target(file_path)

        if validation_error:
            return validation_error

        try:
            original_content = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return {
                "status": "error",
                "message": f"Could not read target file: {exc}",
            }

        # Diagnose without running the program unless approved.
        diagnosis_result = self.diagnose(
            file_path,
            allow_execution=allow_execution,
        )

        if diagnosis_result.get("status") == "success":
            return {
                "status": "not_needed",
                "message": "The program passed the current checks.",
                "diagnosis": diagnosis_result,
            }

        if diagnosis_result.get("status") == "approval_required":
            return {
                "status": "approval_required",
                "message": (
                    "Syntax check passed, but execution was skipped. "
                    "Review the file and retry with allow_execution=True "
                    "if you approve running it."
                ),
                "diagnosis": diagnosis_result,
            }

        if diagnosis_result.get("status") == "rejected":
            return diagnosis_result

        proposal = self.repair_engine.propose_repair(
            original_content=original_content,
            diagnosis=diagnosis_result.get("diagnosis", {}),
            repaired_content=repaired_content,
        )

        if proposal.get("status") != "ready":
            return {
                "status": "rejected",
                "message": "The proposed repair did not pass validation.",
                "proposal": proposal,
            }

        if not confirm:
            return {
                "status": "confirmation_required",
                "message": (
                    "Review the proposal, then call again with "
                    "confirm=True."
                ),
                "proposal": proposal,
                "diagnosis": diagnosis_result,
            }

        apply_result = self.repair_engine.apply_repair(
            file_path=file_path,
            repaired_content=repaired_content,
            confirm=True,
        )

        if apply_result.get("status") != "success":
            return {
                "status": "error",
                "message": "The repair could not be applied.",
                "apply_result": apply_result,
            }

        # Verify syntax without execution unless separately approved.
        verification = self.diagnose(
            file_path,
            allow_execution=allow_execution,
        )

        if verification.get("status") == "approval_required":
            return {
                "status": "repair_applied_verification_pending",
                "message": (
                    "Repair was applied and syntax checking passed. "
                    "Runtime verification was skipped because execution "
                    "was not approved."
                ),
                "apply_result": apply_result,
                "verification": verification,
            }

        return {
            "status": (
                "healed"
                if verification.get("status") == "success"
                else "repair_applied_but_verification_failed"
            ),
            "message": (
                "Repair applied and verification passed."
                if verification.get("status") == "success"
                else "Repair was applied, but verification still reports an error."
            ),
            "apply_result": apply_result,
            "verification": verification,
        }


if __name__ == "__main__":
    agent = SelfHealingAgent()

    print("Self-Healing Agent is ready.")
    print(f"Workspace: {agent.workspace_path}")
    print("Execution requires explicit approval.")
    print("No files were repaired or modified by this startup check.")