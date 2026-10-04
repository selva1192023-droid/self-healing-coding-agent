
import ast
import re
from pathlib import Path


class ErrorDetector:
    """Detect and analyze common Python code errors."""

    def detect_syntax_error(self, file_path):
        """Check a Python file for syntax errors."""
        path = Path(file_path)

        if not path.is_file():
            return {
                "status": "error",
                "error_type": "FileNotFoundError",
                "message": "Python file not found.",
            }

        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path))

            return {
                "status": "success",
                "message": "No syntax errors detected.",
                "file": str(path),
            }

        except SyntaxError as exc:
            return {
                "status": "error",
                "error_type": "SyntaxError",
                "message": exc.msg,
                "file": str(path),
                "line": exc.lineno,
                "column": exc.offset,
                "source_line": exc.text.strip() if exc.text else None,
            }

        except (OSError, UnicodeDecodeError) as exc:
            return {
                "status": "error",
                "error_type": type(exc).__name__,
                "message": str(exc),
                "file": str(path),
            }

    def analyze_execution_result(self, result):
        """Analyze output returned by the code executor."""
        if not isinstance(result, dict):
            return {
                "status": "error",
                "message": "Execution result must be a dictionary.",
            }

        if result.get("status") == "success":
            return {
                "status": "success",
                "message": "Program executed successfully.",
                "stdout": result.get("stdout", ""),
            }

        stderr = result.get("stderr", "")
        message = result.get("message", "")
        error_text = stderr or message or "Unknown execution error"

        error_type = self._extract_error_type(error_text)
        line_number = self._extract_line_number(error_text)

        return {
            "status": "error",
            "error_type": error_type,
            "message": error_text,
            "line": line_number,
            "possible_cause": self._suggest_cause(error_type),
            "stdout": result.get("stdout", ""),
            "return_code": result.get("return_code"),
        }

    @staticmethod
    def _extract_error_type(error_text):
        """Extract the Python exception name from an error message."""
        matches = re.findall(
            r"([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\s*:",
            error_text,
        )
        return matches[-1] if matches else "ExecutionError"

    @staticmethod
    def _extract_line_number(error_text):
        """Extract the last Python traceback line number, if present."""
        matches = re.findall(r'line\s+(\d+)', error_text)
        return int(matches[-1]) if matches else None

    @staticmethod
    def _suggest_cause(error_type):
        """Provide a basic explanation for common Python errors."""
        suggestions = {
            "SyntaxError": "Check Python syntax, punctuation, and indentation.",
            "IndentationError": "Check the indentation of the affected code block.",
            "NameError": "A variable or function may be undefined or misspelled.",
            "TypeError": "Check whether the values and argument types are compatible.",
            "ValueError": "Check whether the supplied value is valid for the operation.",
            "IndexError": "Check list or sequence indexes and their boundaries.",
            "KeyError": "Check whether the requested dictionary key exists.",
            "AttributeError": "Check whether the object has the requested attribute or method.",
            "ImportError": "Check the import statement and package availability.",
            "ModuleNotFoundError": "Check whether the required module is installed and accessible.",
            "ZeroDivisionError": "Check that the divisor is not zero.",
            "FileNotFoundError": "Check the file path and whether the file exists.",
        }

        return suggestions.get(
            error_type,
            "Review the traceback and source code to identify the cause.",
        )


if __name__ == "__main__":
    detector = ErrorDetector()

    print("Testing syntax error detection:")
    print("-" * 35)

    sample_file = Path(__file__).resolve().parent / "sample_error.py"
    sample_file.write_text(
        "def greet():\n"
        "    print('Hello'\n",
        encoding="utf-8",
    )

    syntax_result = detector.detect_syntax_error(sample_file)
    print(syntax_result)

    print("\nTesting execution error analysis:")
    print("-" * 35)

    sample_execution = {
        "status": "error",
        "return_code": 1,
        "stdout": "",
        "stderr": (
            "Traceback (most recent call last):\n"
            '  File "sample_error.py", line 2, in greet\n'
            "    print(undefined_variable)\n"
            "NameError: name 'undefined_variable' is not defined\n"
        ),
    }

    execution_result = detector.analyze_execution_result(
        sample_execution
    )
    print(execution_result)

    sample_file.unlink(missing_ok=True)