"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import List

from ..checks.rhetoric import (
    check_echoed_clauses,
    check_negative_parallelism,
    check_no_chain,
    check_question_answer,
    check_question_density,
    check_tricolon_density,
)
from ..model import Rule


def rules() -> List[Rule]:
    return [
        Rule(
                    "rhetoric.negative-parallelism",
                    "Repeated 'not X, but Y' or 'this is not X; it is Y' reframes",
                    "warning",
                    check_negative_parallelism,
                    defaults={"max": 1, "window_words": 500},
                    strict_defaults={"max": 0, "window_words": 500},
                ),
        Rule(
                    "rhetoric.no-chain",
                    "Three or more 'no X, no Y' items in one chain",
                    "warning",
                    check_no_chain,
                    defaults={"minimum_items": 3},
                    strict_defaults={"minimum_items": 2},
                ),
        Rule(
                    "rhetoric.question-answer",
                    "Repeated staged questions followed by short answers",
                    "warning",
                    check_question_answer,
                    defaults={"max": 1, "window_words": 400, "answer_max_words": 5},
                    strict_defaults={"max": 0},
                ),
        Rule(
                    "rhetoric.question-density",
                    "Too many questions in a short passage",
                    "warning",
                    check_question_density,
                    defaults={"max": 3, "window_words": 500},
                    strict_defaults={"max": 2},
                ),
        Rule(
                    "rhetoric.echoed-clauses",
                    "Three or more parallel clauses repeat the same opening or ending",
                    "warning",
                    check_echoed_clauses,
                    defaults={"minimum_clauses": 3, "maximum_clauses": 5},
                ),
        Rule(
                    "rhetoric.tricolon-density",
                    "Repeated three-part rhetorical lists",
                    "info",
                    check_tricolon_density,
                    defaults={"max": 3, "window_words": 750},
                    strict_severity="warning",
                    strict_defaults={"max": 2},
                ),
    ]
