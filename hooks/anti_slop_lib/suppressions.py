"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple

from .text import line_spans

DIRECTIVE_RE = re.compile(
    r"<!--\s*anti-slop-(disable-next-line|disable|enable|ignore)(?:\s+([^>]*?))?\s*-->",
    re.IGNORECASE,
)

def parse_rule_selectors(value: Optional[str]) -> Set[str]:
    if not value or not value.strip():
        return {"*"}
    return {token for token in re.split(r"[\s,]+", value.strip()) if token}

def rule_selector_matches(selector: str, rule_id: str) -> bool:
    selector = selector.strip()
    if selector in {"*", "all"}:
        return True
    if selector.endswith(".*"):
        return rule_id.startswith(selector[:-1])
    return selector == rule_id

def parse_suppressions(source: str) -> Tuple[List[bool], List[Set[str]]]:
    spans = line_spans(source)
    all_flags: List[bool] = []
    rule_flags: List[Set[str]] = []
    disabled_all = False
    disabled_rules: Set[str] = set()
    pending_all = False
    pending_rules: Set[str] = set()

    for start, end in spans:
        line = source[start:end]
        line_all = disabled_all or pending_all
        line_rules = set(disabled_rules) | set(pending_rules)
        pending_all = False
        pending_rules.clear()

        for match in DIRECTIVE_RE.finditer(line):
            action = match.group(1).lower()
            selectors = parse_rule_selectors(match.group(2))
            selects_all = any(selector in {"*", "all"} for selector in selectors)
            if action == "ignore":
                if selects_all:
                    line_all = True
                else:
                    line_rules.update(selectors)
            elif action == "disable-next-line":
                if selects_all:
                    pending_all = True
                else:
                    pending_rules.update(selectors)
            elif action == "disable":
                if selects_all:
                    disabled_all = True
                else:
                    disabled_rules.update(selectors)
            elif action == "enable":
                if selects_all:
                    disabled_all = False
                    disabled_rules.clear()
                else:
                    disabled_rules.difference_update(selectors)

        all_flags.append(line_all)
        rule_flags.append(line_rules)

    return all_flags, rule_flags
