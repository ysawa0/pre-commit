"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import List

from ..checks.repetition import (
    check_loaded_word_repetition,
    check_paragraph_openers,
    check_sentence_openers,
    check_transition_repetition,
)
from ..model import Rule


def rules() -> List[Rule]:
    return [
        Rule(
                    "repetition.sentence-opener",
                    "Repeated sentence openings",
                    "warning",
                    check_sentence_openers,
                    defaults={"consecutive": 3, "window_sentences": 8, "window_count": 5},
                    strict_defaults={"consecutive": 3, "window_count": 4},
                ),
        Rule(
                    "repetition.paragraph-opener",
                    "Repeated paragraph openings",
                    "warning",
                    check_paragraph_openers,
                    defaults={"consecutive": 3, "window_paragraphs": 6, "window_count": 4},
                    strict_defaults={"window_count": 3},
                ),
        Rule(
                    "repetition.transition",
                    "Repeated stock transition phrases",
                    "warning",
                    check_transition_repetition,
                    defaults={"max": 2, "window_words": 500},
                    strict_defaults={"max": 1},
                ),
        Rule(
                    "repetition.loaded-word",
                    "Repeated high-level adjectives and verbs instead of concrete description",
                    "warning",
                    check_loaded_word_repetition,
                    defaults={"max": 2, "window_words": 500},
                    strict_defaults={"max": 1},
                ),
    ]
