
from pathlib import Path

from repair.self_healing_agent import SelfHealingAgent


def test_invalid_repair():
    workspace = Path(__file__).resolve().parent / "workspace"
    workspace.mkdir(exist_ok=True)

    target = workspace / "repair_test.py"

    # Reset the target to a broken state for a repeatable test.
    broken_code = 'def greet(\n    print("Broken code")\n\ngreet()\n'
    target.write_text(broken_code, encoding="utf-8")

    agent = SelfHealingAgent()

    invalid_code = """def greet(
    print("This code has a syntax error")

greet()
"""

    result = agent.repair_and_verify(
        "repair_test.py",
        invalid_code,
        confirm=True,
    )

    print("\nINVALID REPAIR TEST:")
    print(result)

    assert result["status"] == "rejected", (
        f"Expected rejected, got: {result['status']}"
    )

    # Confirm the original broken file was not modified.
    assert target.read_text(encoding="utf-8") == broken_code

    print("PASS: Invalid repair rejected")
    print("PASS: Broken original file preserved")


def test_valid_repair():
    agent = SelfHealingAgent()

    fixed_code = """def greet():
    print("Hello from self-healing agent")

greet()
"""

    result = agent.repair_and_verify(
        "repair_test.py",
        fixed_code,
        confirm=True,
        allow_execution=True,
    )

    print("\nVALID REPAIR TEST:")
    print(result)

    assert result["status"] == "healed", (
        f"Expected healed, got: {result['status']}"
    )

    print("PASS: Valid repair applied and verified")


if __name__ == "__main__":
    test_invalid_repair()
    test_valid_repair()
    print("\nAll repair tests passed!")