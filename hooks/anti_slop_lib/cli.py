"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional, Sequence

from .config import lint_document, load_config
from .document import Document
from .model import ConfigError, Diagnostic, SEVERITY_ORDER, VERSION
from .output import diagnostic_to_dict, print_github, print_text
from .registry import RULES

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="anti-slop",
        description="Deterministically lint Markdown for canned, repetitive, or bloated prose.",
    )
    parser.add_argument("files", metavar="FILE", nargs="*", help="Markdown or MDX files to lint")
    parser.add_argument("--config", help="Path to .anti-slop.json")
    parser.add_argument("--preset", choices=["recommended", "strict"], help="Override the configured preset")
    parser.add_argument("--format", choices=["text", "json", "github"], default="text")
    parser.add_argument("--fail-level", choices=["info", "warning", "error", "none"], help="Lowest severity that exits 1")
    parser.add_argument("--no-excerpts", action="store_true", help="Do not print source excerpts in text output")
    parser.add_argument("--list-rules", action="store_true", help="List rules and exit")
    parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    return parser.parse_args(argv)

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.list_rules:
        for rule in RULES:
            strict = rule.strict_severity if rule.strict_severity is not None else rule.recommended_severity
            print("{:<38} recommended={:<7} strict={:<7} {}".format(rule.id, rule.recommended_severity, strict, rule.summary))
        return 0
    if not args.files:
        print("anti-slop: no files provided", file=sys.stderr)
        return 2

    try:
        config = load_config(args.config)
        preset = args.preset or config.get("preset", "recommended")
        fail_level = args.fail_level or config.get("fail_level", "warning")
        if fail_level not in {"info", "warning", "error", "none"}:
            raise ConfigError("Invalid fail_level '{}'".format(fail_level))

        documents: Dict[str, Document] = {}
        diagnostics: List[Diagnostic] = []
        for path in args.files:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    source = handle.read()
            except (OSError, UnicodeError) as exc:
                print("anti-slop: cannot read {}: {}".format(path, exc), file=sys.stderr)
                return 2
            document = Document(path, source)
            documents[path] = document
            diagnostics.extend(lint_document(document, preset, config))
        diagnostics.sort(key=lambda item: (item.path, item.start, -SEVERITY_ORDER[item.severity], item.rule_id))
    except ConfigError as exc:
        print("anti-slop: {}".format(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([diagnostic_to_dict(item) for item in diagnostics], indent=2, sort_keys=True))
    elif args.format == "github":
        print_github(diagnostics)
    else:
        print_text(diagnostics, documents, excerpts=not args.no_excerpts)
        if diagnostics:
            counts = {severity: sum(1 for item in diagnostics if item.severity == severity) for severity in ("error", "warning", "info")}
            print(
                "\nanti-slop: {} diagnostic{} ({} error, {} warning, {} info)".format(
                    len(diagnostics),
                    "" if len(diagnostics) == 1 else "s",
                    counts["error"],
                    counts["warning"],
                    counts["info"],
                )
            )

    if fail_level == "none":
        return 0
    threshold = SEVERITY_ORDER[fail_level]
    return 1 if any(SEVERITY_ORDER[item.severity] >= threshold for item in diagnostics) else 0
