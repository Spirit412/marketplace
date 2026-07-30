#!/usr/bin/env python3
"""Pre-commit hook: enforce minimum variable name length of 4 characters.

Exceptions cover Python idioms: loop counters, exception vars, common abbreviations,
ORM/API field names, and enum members.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

MIN_LENGTH = 4
ALLOWED: set[str] = {
    # Loop / iteration
    "_", "i", "j", "k", "v",
    # Exception handling
    "e", "ex", "err", "exc",
    # Type parameters / classmethod
    "T", "cls",
    # Universal DB/API field
    "id",
    # Common abbreviations
    "app", "key", "url", "row", "now", "msg", "raw",
    "sku", "tax", "lft", "rgt", "ttl", "dsn", "fmt",
    "uid", "ws", "doc", "job", "qs", "tpl", "img",
    # JWT claims
    "jti", "iat", "exp",
    # Enum members (uppercase short names are intentional)
    "ALL", "INT", "CSV", "PDF", "RU", "US", "EU", "sms",
    # Domain-specific
    "wb",  # openpyxl workbook
}


class VarNameChecker(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.errors: list[str] = []

    def _check_name(self, name: str, lineno: int, col_offset: int) -> None:
        if len(name) < MIN_LENGTH and name not in ALLOWED and not name.startswith("_"):
            self.errors.append(
                f"{self.filename}:{lineno}:{col_offset}: "
                f"name '{name}' too short ({len(name)} < {MIN_LENGTH})"
            )

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self._check_name(node.id, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for arg in node.args.args:
            self._check_name(arg.arg, node.lineno, node.col_offset)
        for arg in node.args.posonlyargs:
            self._check_name(arg.arg, node.lineno, node.col_offset)
        if node.args.vararg:
            self._check_name(node.args.vararg.arg, node.lineno, node.col_offset)
        if node.args.kwarg:
            self._check_name(node.args.kwarg.arg, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._check_name(node.name, node.lineno, node.col_offset)
        self.generic_visit(node)


def check_file(filepath: str) -> list[str]:
    try:
        with open(filepath) as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        checker = VarNameChecker(filepath)
        checker.visit(tree)
        return checker.errors
    except SyntaxError:
        return []


def main() -> int:
    exit_code = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_dir():
            for py_file in path.rglob("*.py"):
                if ".venv" in str(py_file):
                    continue
                errors = check_file(str(py_file))
                for err in errors:
                    print(err)
                    exit_code = 1
        elif path.suffix == ".py":
            errors = check_file(str(path))
            for err in errors:
                print(err)
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
