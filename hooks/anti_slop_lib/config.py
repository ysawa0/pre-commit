"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .document import Document
from .model import ConfigError, Diagnostic, Rule, SEVERITY_ORDER
from .registry import RULES, RULES_BY_ID

def load_config(path: Optional[str]) -> Dict[str, Any]:
    candidate = path
    if candidate is None:
        default_path = os.path.join(os.getcwd(), ".anti-slop.json")
        if os.path.isfile(default_path):
            candidate = default_path
    if candidate is None:
        return {}
    try:
        with open(candidate, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise ConfigError("Cannot read config {}: {}".format(candidate, exc))
    except ValueError as exc:
        raise ConfigError("Invalid JSON in {}: {}".format(candidate, exc))
    if not isinstance(data, dict):
        raise ConfigError("Config root must be a JSON object")
    unknown = set(data) - {"preset", "fail_level", "rules"}
    if unknown:
        raise ConfigError("Unknown config keys: {}".format(", ".join(sorted(unknown))))
    preset = data.get("preset")
    if preset is not None and (not isinstance(preset, str) or preset not in {"recommended", "strict"}):
        raise ConfigError("'preset' must be 'recommended' or 'strict'")
    fail_level = data.get("fail_level")
    if fail_level is not None and (
        not isinstance(fail_level, str) or fail_level not in {"info", "warning", "error", "none"}
    ):
        raise ConfigError("'fail_level' must be info, warning, error, or none")
    rules = data.get("rules", {})
    if not isinstance(rules, dict):
        raise ConfigError("'rules' must be a JSON object")
    unknown_rules = set(rules) - set(RULES_BY_ID)
    if unknown_rules:
        raise ConfigError("Unknown rules: {}".format(", ".join(sorted(unknown_rules))))
    return data

INTEGER_OPTIONS = {
    "max",
    "window_words",
    "minimum_items",
    "answer_max_words",
    "minimum_clauses",
    "maximum_clauses",
    "consecutive",
    "window_sentences",
    "window_count",
    "window_paragraphs",
    "max_words",
    "minimum_run",
    "minimum_sentences",
    "minimum_headings",
    "min_words_per_heading",
}

def validate_rule_options(rule_id: str, options: Mapping[str, Any]) -> None:
    for name, value in options.items():
        if name == "maximum_cv":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ConfigError("Rule '{}' option '{}' must be a positive number".format(rule_id, name))
            continue
        if name not in INTEGER_OPTIONS:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError("Rule '{}' option '{}' must be an integer".format(rule_id, name))
        minimum = 0 if name == "max" else 1
        if value < minimum:
            qualifier = "non-negative" if minimum == 0 else "positive"
            raise ConfigError("Rule '{}' option '{}' must be {}".format(rule_id, name, qualifier))
    if options.get("minimum_clauses", 1) > options.get("maximum_clauses", sys.maxsize):
        raise ConfigError("Rule '{}' requires minimum_clauses <= maximum_clauses".format(rule_id))

def resolve_rule_settings(rule: Rule, preset: str, config: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
    if preset not in {"recommended", "strict"}:
        raise ConfigError("Unknown preset '{}'; expected recommended or strict".format(preset))
    severity = rule.recommended_severity
    options = dict(rule.defaults)
    if preset == "strict":
        if rule.strict_severity is not None:
            severity = rule.strict_severity
        options.update(rule.strict_defaults)

    override = config.get("rules", {}).get(rule.id)
    if isinstance(override, str):
        severity = override
    elif isinstance(override, dict):
        override = dict(override)
        if "severity" in override:
            severity = override.pop("severity")
        allowed_options = set(rule.defaults) | set(rule.strict_defaults)
        unknown_options = set(override) - allowed_options
        if unknown_options:
            raise ConfigError(
                "Rule '{}' has unknown options: {}".format(rule.id, ", ".join(sorted(unknown_options)))
            )
        options.update(override)
    elif override is not None:
        raise ConfigError("Rule '{}' must be a severity string or JSON object".format(rule.id))

    if not isinstance(severity, str) or severity not in SEVERITY_ORDER:
        raise ConfigError("Rule '{}' has invalid severity '{}'".format(rule.id, severity))
    validate_rule_options(rule.id, options)
    return severity, options

def lint_document(document: Document, preset: str, config: Mapping[str, Any]) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    for rule in RULES:
        severity, options = resolve_rule_settings(rule, preset, config)
        if severity == "off":
            continue
        try:
            findings = rule.checker(document, options)
        except (TypeError, ValueError) as exc:
            raise ConfigError("Invalid options for '{}': {}".format(rule.id, exc))
        for finding in findings:
            if document.is_suppressed(finding.start, rule.id):
                continue
            line, column = document.location(finding.start)
            end_line, end_column = document.location(max(finding.start, finding.end - 1))
            diagnostics.append(
                Diagnostic(
                    path=document.path,
                    rule_id=rule.id,
                    severity=severity,
                    message=finding.message,
                    start=finding.start,
                    end=finding.end,
                    line=line,
                    column=column,
                    end_line=end_line,
                    end_column=end_column + 1,
                    suggestion=finding.suggestion,
                )
            )
    diagnostics.sort(key=lambda item: (item.path, item.start, -SEVERITY_ORDER[item.severity], item.rule_id))
    return diagnostics
