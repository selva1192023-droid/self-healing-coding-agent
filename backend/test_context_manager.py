
import tempfile
from pathlib import Path

from code_engine.context_manager import ContextManager


def test_valid_target_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        target = root / "sample.py"
        target.write_text("print('Hello')\n", encoding="utf-8")

        result = ContextManager(str(root)).build_context("sample.py")

        assert result["status"] == "success"
        assert result["target_file"] == "sample.py"
        assert result["file_content"] == "print('Hello')\n"
        assert result["code_structure"]["status"] == "success"

        print("PASS: Valid target file accepted")


def test_outside_project_path_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        outside = root.parent / f"{root.name}_outside.py"

        try:
            outside.write_text("print('outside')\n", encoding="utf-8")

            result = ContextManager(str(root)).build_context(
                f"../{outside.name}"
            )

            assert result["status"] == "error"
            assert result["message"] == (
                "Target file must be inside the project."
            )

            print("PASS: Outside-project path rejected")
        finally:
            outside.unlink(missing_ok=True)


def test_non_python_target_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        target = root / "notes.txt"
        target.write_text("Some notes\n", encoding="utf-8")

        result = ContextManager(str(root)).build_context("notes.txt")

        assert result["status"] == "error"
        assert result["message"] == (
            "Only Python target files are supported."
        )

        print("PASS: Non-Python target rejected")


def test_missing_target_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = ContextManager(temp_dir).build_context("missing.py")

        assert result["status"] == "error"
        assert result["message"] == (
            "Target Python file does not exist."
        )

        print("PASS: Missing target rejected")


if __name__ == "__main__":
    test_valid_target_file()
    test_outside_project_path_rejected()
    test_non_python_target_rejected()
    test_missing_target_rejected()

    print("\nAll context manager tests passed!")