"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import statistics
from typing import Any, List, Mapping

from ..document import Document
from ..model import Finding

def check_short_sentence_run(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    max_words = int(options.get("max_words", 5))
    minimum_run = int(options.get("minimum_run", 3))
    findings: List[Finding] = []
    for section_units in document.units_by_section(document.sentences):
        index = 0
        while index < len(section_units):
            if section_units[index].word_count > max_words:
                index += 1
                continue
            end = index + 1
            while end < len(section_units) and section_units[end].word_count <= max_words:
                end += 1
            if end - index >= minimum_run:
                units = section_units[index:end]
                findings.append(
                    Finding(
                        units[1].start,
                        units[-1].end,
                        "{} consecutive sentences contain at most {} words each, creating a manufactured staccato rhythm.".format(
                            len(units), max_words
                        ),
                        "Combine related fragments and reserve the short sentence for emphasis.",
                    )
                )
            index = end
    return findings

def check_uniform_sentence_length(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    minimum_sentences = int(options.get("minimum_sentences", 10))
    lengths = [sentence.word_count for sentence in document.sentences if sentence.word_count >= 3]
    if len(lengths) < minimum_sentences:
        return []
    mean = statistics.mean(lengths)
    if mean <= 0:
        return []
    coefficient = statistics.pstdev(lengths) / mean
    maximum_cv = float(options.get("maximum_cv", 0.18))
    if coefficient >= maximum_cv:
        return []
    start = document.sentences[0].start
    end = document.sentences[-1].end
    return [
        Finding(
            start,
            end,
            "Sentence lengths are unusually uniform (coefficient of variation {:.2f} across {} sentences).".format(
                coefficient, len(lengths)
            ),
            "Mix short assertions with longer explanatory sentences where the content supports it.",
        )
    ]
