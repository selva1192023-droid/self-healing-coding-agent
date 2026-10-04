
import ast
from pathlib import Path
from typing import Any


def parse_python_code(source_code: str, filename: str = "<unknown>") -> dict[str, Any]:
    """
    Analyze Python source code and extract imports,
    functions, classes, and their line numbers.
    """
    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as exc:
        return {
            "status": "error",
            "filename": filename,
            "message": f"Syntax error at line {exc.lineno}: {exc.msg}",
        }

    imports = []
    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                })

        elif isinstance(node, ast.ImportFrom):
            imports.append({
                "module": node.module,
                "names": [
                    {
                        "name": alias.name,
                        "alias": alias.asname,
                    }
                    for alias in node.names
                ],
                "line": node.lineno,
            })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "type": (
                    "async_function"
                    if isinstance(node, ast.AsyncFunctionDef)
                    else "function"
                ),
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", None),
                "parameters": [
                    arg.arg for arg in node.args.args
                ],
                "decorators": [
                    ast.unparse(decorator)
                    for decorator in node.decorator_list
                ],
            })

        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", None),
                "bases": [
                    ast.unparse(base)
                    for base in node.bases
                ],
                "methods": [
                    child.name
                    for child in node.body
                    if isinstance(
                        child,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                ],
            })

    return {
        "status": "success",
        "filename": filename,
        "total_imports": len(imports),
        "total_functions": len(functions),
        "total_classes": len(classes),
        "imports": imports,
        "functions": functions,
        "classes": classes,
    }


def parse_python_file(file_path: str) -> dict[str, Any]:
    """Read and parse a Python source file."""
    path = Path(file_path)

    if not path.is_file():
        return {
            "status": "error",
            "filename": str(path),
            "message": "File does not exist.",
        }

    if path.suffix.lower() != ".py":
        return {
            "status": "error",
            "filename": str(path),
            "message": "Only Python (.py) files are supported.",
        }

    try:
        source_code = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "status": "error",
            "filename": str(path),
            "message": f"Could not read file: {exc}",
        }

    return parse_python_code(source_code, filename=str(path))


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m code_engine.code_parser <python_file>")
        raise SystemExit(1)

    result = parse_python_file(sys.argv[1])
    print(json.dumps(result, indent=2))