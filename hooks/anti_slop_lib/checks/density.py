"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import Any, List, Mapping, Sequence

from ..document import Document
from ..model import Finding
from ..rule_utils import cluster_offsets

def check_density_from_offsets(
    document: Document,
    offsets: Sequence[int],
    options: Mapping[str, Any],
    noun: str,
    suggestion: str,
) -> List[Finding]:
    max_occurrences = int(options.get("max", 4))
    window_words = int(options.get("window_words", 500))
    return [
        Finding(
            cluster[max_occurrences],
            cluster[-1] + 1,
            "{} {} appear within {} words.".format(len(cluster), noun, window_words),
            suggestion,
        )
        for cluster in cluster_offsets(document, offsets, max_occurrences=max_occurrences, window_words=window_words)
    ]

def check_em_dash_density(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    offsets = [match.start() for match in re.finditer("—", document.visible)]
    return check_density_from_offsets(
        document,
        offsets,
        options,
        "em dashes",
        "Keep the strongest interruption and use commas, parentheses, or separate sentences elsewhere.",
    )

def check_bold_density(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    return check_density_from_offsets(
        document,
        [span.start for span in document.bold_spans],
        options,
        "bold spans",
        "Use emphasis only where the reader genuinely needs a visual anchor.",
    )

def check_parenthetical_density(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    return check_density_from_offsets(
        document,
        [span.start for span in document.parenthetical_spans],
        options,
        "parenthetical asides",
        "Move necessary context into the sentence and delete dispensable asides.",
    )

def check_heading_density(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    minimum_headings = int(options.get("minimum_headings", 6))
    min_words_per_heading = int(options.get("min_words_per_heading", 70))
    count = len(document.heading_spans)
    if count < minimum_headings or not document.word_count:
        return []
    words_per_heading = document.word_count / float(count)
    if words_per_heading >= min_words_per_heading:
        return []
    return [
        Finding(
            document.heading_spans[1].start if len(document.heading_spans) > 1 else document.heading_spans[0].start,
            document.heading_spans[-1].end,
            "{} headings divide {} words, or only {:.0f} words per heading.".format(count, document.word_count, words_per_heading),
            "Merge sections whose headings promise more structure than the content delivers.",
        )
    ]
