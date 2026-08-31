"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import List

from ..checks.density import (
    check_bold_density,
    check_em_dash_density,
    check_heading_density,
    check_parenthetical_density,
)
from ..model import Rule


def rules() -> List[Rule]:
    return [
        Rule(
                    "density.em-dash",
                    "High em-dash density",
                    "warning",
                    check_em_dash_density,
                    defaults={"max": 4, "window_words": 500},
                    strict_defaults={"max": 3},
                ),
        Rule(
                    "density.bold",
                    "High bold-emphasis density",
                    "warning",
                    check_bold_density,
                    defaults={"max": 10, "window_words": 500},
                    strict_defaults={"max": 6},
                ),
        Rule(
                    "density.parenthetical",
                    "High parenthetical-aside density",
                    "off",
                    check_parenthetical_density,
                    defaults={"max": 6, "window_words": 500},
                    strict_severity="info",
                    strict_defaults={"max": 5},
                ),
        Rule(
                    "structure.heading-density",
                    "Many headings relative to the amount of prose",
                    "off",
                    check_heading_density,
                    defaults={"minimum_headings": 6, "min_words_per_heading": 70},
                    strict_severity="info",
                ),
    ]
