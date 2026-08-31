"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import List

from ..checks.rhythm import check_short_sentence_run, check_uniform_sentence_length
from ..model import Rule


def rules() -> List[Rule]:
    return [
        Rule(
                    "rhythm.short-sentence-run",
                    "A run of very short sentences used as synthetic emphasis",
                    "warning",
                    check_short_sentence_run,
                    defaults={"max_words": 5, "minimum_run": 3},
                    strict_defaults={"max_words": 6},
                ),
        Rule(
                    "rhythm.uniform-sentence-length",
                    "Suspiciously uniform sentence lengths across a document",
                    "off",
                    check_uniform_sentence_length,
                    defaults={"minimum_sentences": 10, "maximum_cv": 0.18},
                    strict_severity="info",
                ),
    ]
