import tempfile
from pathlib import Path

from code_engine.project_scanner import scan_project


def test_sensitive_files_are_excluded():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        safe_file = root / "main.py"
        safe_file.write_text("print('safe')", encoding="utf-8")

        sensitive_files = [
            ".env",
            ".env.development",
            "credentials",
            "secrets.json",
            "private.pem",
            "server.key",
        ]

        for filename in sensitive_files:
            (root / filename).write_text(
                "sensitive test content",
                encoding="utf-8",
            )

        result = scan_project(str(root))

        assert result["status"] == "success"
        discovered = {
            item["name"] for item in result["files"]
        }

        assert "main.py" in discovered

        for filename in sensitive_files:
            assert filename not in discovered, (
                f"Sensitive file was listed: {filename}"
            )

        print("PASS: Sensitive filenames excluded")


def test_ignored_directories_are_skipped():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        (root / "main.py").write_text(
            "print('safe')",
            encoding="utf-8",
        )

        ignored_dir = root / ".venv"
        ignored_dir.mkdir()
        (ignored_dir / "hidden.py").write_text(
            "print('hidden')",
            encoding="utf-8",
        )

        result = scan_project(str(root))

        discovered = {
            item["path"].replace("\\", "/")
            for item in result["files"]
        }

        assert "main.py" in discovered
        assert ".venv/hidden.py" not in discovered

        print("PASS: Ignored directories skipped")


def test_symlink_files_are_skipped():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        outside = root.parent / f"{root.name}_outside.py"

        try:
            outside.write_text(
                "print('outside')",
                encoding="utf-8",
            )

            link = root / "linked.py"

            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                print(
                    "SKIP: Symlink creation unavailable:",
                    exc,
                )
                return

            result = scan_project(str(root))

            discovered = {
                item["name"] for item in result["files"]
            }

            assert "linked.py" not in discovered

            print("PASS: Symlink files skipped")

        finally:
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    test_sensitive_files_are_excluded()
    test_ignored_directories_are_skipped()
    test_symlink_files_are_skipped()
    print("\nScanner security tests completed.")