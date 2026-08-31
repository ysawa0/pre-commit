"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from ..document import Document
from ..model import Finding, TextUnit, WORD_RE
from ..rule_utils import cluster_offsets

def opener_key(text: str, word_count: int = 2) -> Optional[str]:
    words = [match.group(0).lower().replace("’", "'") for match in WORD_RE.finditer(text)]
    if len(words) < word_count:
        return None
    return " ".join(words[:word_count])

def repeated_openers(
    units: Sequence[TextUnit],
    *,
    consecutive: int,
    window_units: int,
    window_count: int,
) -> List[Tuple[str, List[TextUnit]]]:
    results: List[Tuple[str, List[TextUnit]]] = []
    keys = [opener_key(unit.text) for unit in units]
    consumed: Set[int] = set()

    index = 0
    while index < len(units):
        key = keys[index]
        if key is None:
            index += 1
            continue
        end = index + 1
        while end < len(units) and keys[end] == key:
            end += 1
        if end - index >= consecutive:
            results.append((key, list(units[index:end])))
            consumed.update(range(index, end))
        index = end

    for start in range(len(units)):
        end = min(len(units), start + window_units)
        grouped: Dict[str, List[Tuple[int, TextUnit]]] = {}
        for index in range(start, end):
            key = keys[index]
            if key is None or index in consumed:
                continue
            grouped.setdefault(key, []).append((index, units[index]))
        for key, pairs in grouped.items():
            if len(pairs) >= window_count:
                indices = [pair[0] for pair in pairs]
                if min(indices) != start:
                    continue
                results.append((key, [pair[1] for pair in pairs]))
                consumed.update(indices)
    return results

def check_sentence_openers(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    groups: List[Tuple[str, List[TextUnit]]] = []
    for section_units in document.units_by_section(document.sentences):
        groups.extend(
            repeated_openers(
                section_units,
                consecutive=int(options.get("consecutive", 3)),
                window_units=int(options.get("window_sentences", 8)),
                window_count=int(options.get("window_count", 4)),
            )
        )
    return [
        Finding(
            units[1].start,
            units[-1].end,
            "{} sentences repeatedly open with '{}'.".format(len(units), key),
            "Merge a sentence or vary the grammatical opening unless the repetition is deliberate anaphora.",
        )
        for key, units in groups
    ]

def check_paragraph_openers(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    groups: List[Tuple[str, List[TextUnit]]] = []
    for section_units in document.units_by_section(document.paragraphs):
        groups.extend(
            repeated_openers(
                section_units,
                consecutive=int(options.get("consecutive", 3)),
                window_units=int(options.get("window_paragraphs", 6)),
                window_count=int(options.get("window_count", 3)),
            )
        )
    return [
        Finding(
            units[1].start,
            units[-1].end,
            "{} paragraphs repeatedly open with '{}'.".format(len(units), key),
            "Vary the paragraph entry or combine paragraphs that make the same move.",
        )
        for key, units in groups
    ]

def check_transition_repetition(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    transitions = [
        "moreover",
        "furthermore",
        "additionally",
        "in addition",
        "ultimately",
        "in essence",
        "at its core",
        "that said",
        "on the other hand",
        "the key takeaway",
        "here's the thing",
        "here is the thing",
    ]
    positions: Dict[str, List[int]] = {}
    for phrase in transitions:
        pattern = re.compile(r"(?:(?<=^)|(?<=[.!?]))\s*" + re.escape(phrase) + r"\b", re.IGNORECASE | re.MULTILINE)
        positions[phrase] = [match.start() for match in pattern.finditer(document.visible)]

    max_occurrences = int(options.get("max", 2))
    window_words = int(options.get("window_words", 500))
    findings: List[Finding] = []
    for phrase, offsets in positions.items():
        for cluster in cluster_offsets(document, offsets, max_occurrences=max_occurrences, window_words=window_words):
            findings.append(
                Finding(
                    cluster[max_occurrences],
                    cluster[-1] + len(phrase),
                    "The transition '{}' appears {} times within {} words.".format(phrase, len(cluster), window_words),
                    "Delete a transition where the paragraph order already makes the relationship clear.",
                )
            )
    return findings

def check_loaded_word_repetition(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    stems = {
        "delve": r"\bdelv(?:e|es|ed|ing)\b",
        "pivotal": r"\bpivotal\b",
        "nuanced": r"\bnuanced?\b",
        "robust": r"\brobust\b",
        "seamless": r"\bseamless(?:ly)?\b",
        "transformative": r"\btransformative\b",
        "landscape": r"\blandscape\b",
        "tapestry": r"\btapestry\b",
        "underscore": r"\bunderscor(?:e|es|ed|ing)\b",
        "showcase": r"\bshowcas(?:e|es|ed|ing)\b",
        "foster": r"\bfoster(?:s|ed|ing)?\b",
        "elevate": r"\belevat(?:e|es|ed|ing)\b",
        "unlock": r"\bunlock(?:s|ed|ing)?\b",
    }
    max_occurrences = int(options.get("max", 2))
    window_words = int(options.get("window_words", 500))
    findings: List[Finding] = []
    for label, pattern_text in stems.items():
        matches = list(re.finditer(pattern_text, document.visible, re.IGNORECASE))
        for cluster in cluster_offsets(
            document,
            [match.start() for match in matches],
            max_occurrences=max_occurrences,
            window_words=window_words,
        ):
            findings.append(
                Finding(
                    cluster[max_occurrences],
                    cluster[-1] + len(label),
                    "The loaded word '{}' appears {} times within {} words.".format(label, len(cluster), window_words),
                    "Replace at least one use with the concrete property you mean.",
                )
            )
    return findings
