"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import Dict, List

from .catalogs.density import rules as density_rules
from .catalogs.repetition import rules as repetition_rules
from .catalogs.rhetoric import rules as rhetoric_rules
from .catalogs.rhythm import rules as rhythm_rules
from .catalogs.style import rules as style_rules
from .catalogs.words import rules as word_rules
from .model import Rule


def build_rules() -> List[Rule]:
    return (
        word_rules()
        + style_rules()
        + rhetoric_rules()
        + repetition_rules()
        + rhythm_rules()
        + density_rules()
    )


RULES = build_rules()
RULES_BY_ID: Dict[str, Rule] = {rule.id: rule for rule in RULES}
