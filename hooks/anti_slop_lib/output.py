"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

from .document import Document
from .model import Diagnostic

def diagnostic_to_dict(diagnostic: Diagnostic) -> Dict[str, Any]:
    return {
        "path": diagnostic.path,
        "line": diagnostic.line,
        "column": diagnostic.column,
        "end_line": diagnostic.end_line,
        "end_column": diagnostic.end_column,
        "severity": diagnostic.severity,
        "rule": diagnostic.rule_id,
        "message": diagnostic.message,
        "suggestion": diagnostic.suggestion,
    }

def github_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A").replace(":", "%3A").replace(",", "%2C")

def print_text(diagnostics: Sequence[Diagnostic], documents: Mapping[str, Document], excerpts: bool = True) -> None:
    for diagnostic in diagnostics:
        print(
            "{}:{}:{}: {} [{}] {}".format(
                diagnostic.path,
                diagnostic.line,
                diagnostic.column,
                diagnostic.severity,
                diagnostic.rule_id,
                diagnostic.message,
            )
        )
        if diagnostic.suggestion:
            print("  suggestion: {}".format(diagnostic.suggestion))
        if excerpts:
            excerpt = documents[diagnostic.path].excerpt(diagnostic.line)
            if excerpt:
                print("  {}".format(excerpt.rstrip()))
                caret_width = max(1, min(len(excerpt) - diagnostic.column + 2, diagnostic.end_column - diagnostic.column))
                print("  {}{}".format(" " * (diagnostic.column - 1), "^" * caret_width))

def print_github(diagnostics: Sequence[Diagnostic]) -> None:
    for diagnostic in diagnostics:
        level = "error" if diagnostic.severity == "error" else "warning" if diagnostic.severity == "warning" else "notice"
        message = diagnostic.message
        if diagnostic.suggestion:
            message += " Suggestion: " + diagnostic.suggestion
        print(
            "::{} file={},line={},col={},endLine={},endColumn={},title={}::{}".format(
                level,
                github_escape(diagnostic.path),
                diagnostic.line,
                diagnostic.column,
                diagnostic.end_line,
                diagnostic.end_column,
                github_escape("anti-slop/" + diagnostic.rule_id),
                github_escape(message),
            )
        )
