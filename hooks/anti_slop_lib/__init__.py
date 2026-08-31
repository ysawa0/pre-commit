"""Public API for anti-slop."""

from .config import lint_document, load_config
from .document import Document
from .model import ConfigError, Diagnostic, Finding, Rule, VERSION
from .registry import RULES, RULES_BY_ID

__all__ = [
    "ConfigError",
    "Diagnostic",
    "Document",
    "Finding",
    "RULES",
    "RULES_BY_ID",
    "Rule",
    "VERSION",
    "lint_document",
    "load_config",
]
