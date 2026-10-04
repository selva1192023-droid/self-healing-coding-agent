
from pathlib import Path
from repair.repair_engine import RepairEngine


def test_invalid_repair_preserves_original():
    workspace = Path(__file__).resolve().parent / "workspace"
    workspace.mkdir(exist_ok=True)

    test_file = workspace / "safety_test.py"
    original_content = 'print("Original file")\n'
    invalid_repair = 'def greet(\n    print("Broken")\n'

    test_file.write_text(original_content, encoding="utf-8")
    engine = RepairEngine(workspace)

    result = engine.apply_repair(
        "safety_test.py",
        invalid_repair,
        confirm=True,
    )

    current_content = test_file.read_text(encoding="utf-8")

    assert result["status"] == "rejected"
    assert current_content == original_content

    print("PASS: Invalid repair rejected")
    print("PASS: Original file preserved")


def test_valid_repair_creates_backup():
    workspace = Path(__file__).resolve().parent / "workspace"
    test_file = workspace / "safety_test.py"

    original_content = 'print("Original file")\n'
    repaired_content = 'print("Repaired file")\n'

    test_file.write_text(original_content, encoding="utf-8")
    engine = RepairEngine(workspace)

    result = engine.apply_repair(
        "safety_test.py",
        repaired_content,
        confirm=True,
    )

    backup_path = test_file.with_suffix(".py.bak")

    assert result["status"] == "success"
    assert test_file.read_text(encoding="utf-8") == repaired_content
    assert backup_path.is_file()
    assert backup_path.read_text(encoding="utf-8") == original_content

    print("PASS: Valid repair applied")
    print("PASS: Backup created")
    print("PASS: Backup contains original code")


def test_rejects_outside_workspace():
    workspace = Path(__file__).resolve().parent / "workspace"
    engine = RepairEngine(workspace)

    try:
        engine.apply_repair(
            "../outside.py",
            'print("Should not be applied")\n',
            confirm=True,
        )
    except ValueError as exc:
        assert "outside the workspace" in str(exc)
        print("PASS: Outside-workspace repair rejected")
    else:
        raise AssertionError(
            "Expected the repair engine to reject an outside path."
        )


if __name__ == "__main__":
    test_invalid_repair_preserves_original()
    test_valid_repair_creates_backup()
    test_rejects_outside_workspace()

    print("\nAll safety tests passed!")