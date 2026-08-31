"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .document import Document

VERSION = "0.2.0"

SEVERITY_ORDER = {"off": -1, "info": 0, "warning": 1, "error": 2}

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[’'][A-Za-z0-9]+)*(?:-[A-Za-z0-9]+)*")

@dataclass(frozen=True)
class Span:
    start: int
    end: int

@dataclass(frozen=True)
class Word:
    text: str
    normalized: str
    start: int
    end: int

@dataclass(frozen=True)
class TextUnit:
    start: int
    end: int
    text: str
    word_count: int

@dataclass(frozen=True)
class Finding:
    start: int
    end: int
    message: str
    suggestion: Optional[str] = None

@dataclass(frozen=True)
class Diagnostic:
    path: str
    rule_id: str
    severity: str
    message: str
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int
    suggestion: Optional[str] = None

@dataclass(frozen=True)
class Rule:
    id: str
    summary: str
    recommended_severity: str
    checker: Callable[["Document", Mapping[str, Any]], List[Finding]]
    defaults: Dict[str, Any] = field(default_factory=dict)
    strict_severity: Optional[str] = None
    strict_defaults: Dict[str, Any] = field(default_factory=dict)

class ConfigError(ValueError):
    pass
