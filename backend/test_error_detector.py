import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from testing.error_detector import ErrorDetector


def test_syntax_error():
    detector = ErrorDetector()

    result = detector.detect_syntax_error(
        "workspace/invalid_syntax.py"
    )

    assert result["status"] == "error"
    assert result["error_type"] == "SyntaxError"

    print("PASS: Syntax error detection")


def test_valid_python():
    detector = ErrorDetector()

    result = detector.detect_syntax_error(
        "workspace/valid_code.py"
    )

    assert result["status"] == "success"

    print("PASS: Valid Python detection")


def test_runtime_error():
    detector = ErrorDetector()

    result = {
        "status": "error",
        "return_code": 1,
        "stdout": "",
        "stderr": "NameError: name 'unknown_variable' is not defined",
    }

    diagnosis = detector.analyze_execution_result(result)

    assert diagnosis["status"] == "error"

    print("PASS: Runtime error diagnosis")


if __name__ == "__main__":
    test_syntax_error()
    test_valid_python()
    test_runtime_error()

    print("\nAll tests passed!")