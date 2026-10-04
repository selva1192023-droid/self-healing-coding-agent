from code_engine.context_manager import ContextManager


def test_additional_source_context():
    print("\n========== SOURCE CONTEXT TEST ==========\n")

    manager = ContextManager(".")

    result = manager.build_context(
        target_file="workspace/hello.py"
    )

    # 1. Check context build status
    assert result.get("status") == "success", (
        f"Context build failed: {result}"
    )
    print("PASS: Context built successfully")

    # 2. Check additional source files
    source_files = result.get("source_files")

    assert isinstance(source_files, dict), (
        "source_files is missing or is not a dictionary"
    )
    print("PASS: Additional source files collected")

    # 3. Check that at least one source file was collected
    assert len(source_files) > 0, (
        "No additional Python source files were collected"
    )
    print(f"PASS: {len(source_files)} additional source file(s) collected")

    # 4. Check that each collected source has text content
    for file_name, content in source_files.items():
        assert isinstance(file_name, str), (
            "A source filename is not a string"
        )
        assert isinstance(content, str), (
            f"Source content for {file_name} is not text"
        )
        assert content.strip(), (
            f"Source file {file_name} has empty content"
        )

    print("PASS: Collected source files contain text")

    # 5. Check that the target file is not duplicated
    target_file = result.get("target_file")

    assert target_file not in source_files, (
        "Target file was duplicated in additional source files"
    )
    print("PASS: Target file excluded from additional sources")

    # 6. Display collected filenames and read errors
    print("\nCollected source filenames:")
    for file_name in source_files:
        print(f" - {file_name}")

    errors = result.get("source_file_errors", [])
    print(f"\nSource read errors: {len(errors)}")

    for error in errors:
        print(f" - {error}")

    print("\nALL SOURCE CONTEXT TESTS PASSED!")


if __name__ == "__main__":
    test_additional_source_context()