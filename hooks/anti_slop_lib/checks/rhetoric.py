"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping

from ..document import Document
from ..model import Finding, Span, WORD_RE
from ..rule_utils import cluster_offsets
from ..text import dedupe_overlapping, normalize_space

def check_negative_parallelism(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    patterns = [
        re.compile(
            r"\b(?:this|that|it|[A-Z][A-Za-z0-9' -]{0,35})\s+(?:isn't|is not|wasn't|was not)\s+"
            r"(?:just\s+)?[^.!?\n]{2,100}[.!?]\s+(?:it(?:'s| is| was)|this is|that(?:'s| is))\s+[^.!?\n]{2,120}",
            re.IGNORECASE,
        ),
        re.compile(r"\bnot\s+(?:just\s+)?[^,.;!?\n]{2,80},?\s+(?:but|rather)\s+[^.;!?\n]{2,110}", re.IGNORECASE),
        re.compile(
            r"\b(?:isn't|is not|wasn't|was not)\s+[^.;!?\n]{2,80}\s*[—–-]\s*(?:it(?:'s| is)|this is|that(?:'s| is))\b",
            re.IGNORECASE,
        ),
    ]
    spans = dedupe_overlapping([Span(match.start(), match.end()) for pattern in patterns for match in pattern.finditer(document.visible)])
    max_occurrences = int(options.get("max", 1))
    window_words = int(options.get("window_words", 500))
    findings: List[Finding] = []
    for cluster in cluster_offsets(document, [span.start for span in spans], max_occurrences=max_occurrences, window_words=window_words):
        findings.append(
            Finding(
                cluster[max_occurrences],
                next((span.end for span in spans if span.start == cluster[-1]), cluster[-1] + 1),
                "{} contrast reframes appear within {} words; repeated 'not X, but Y' structure starts to sound manufactured.".format(
                    len(cluster), window_words
                ),
                "State at least one positive claim directly, or keep only the strongest contrast.",
            )
        )
    return findings

def check_no_chain(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    minimum_items = int(options.get("minimum_items", 3))
    pattern = re.compile(r"\bno\s+[^,.;:!?\n]{1,45}(?:\s*,\s*no\s+[^,.;:!?\n]{1,45})+", re.IGNORECASE)
    findings: List[Finding] = []
    for match in pattern.finditer(document.visible):
        item_count = len(re.findall(r"\bno\s+", match.group(0), re.IGNORECASE))
        if item_count >= minimum_items:
            findings.append(
                Finding(
                    match.start(),
                    match.end(),
                    "A {}-item 'no X, no Y' chain performs emphasis without adding evidence.".format(item_count),
                    "Replace the chain with the specific positive claim.",
                )
            )
    return findings

def check_question_answer(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    offsets: List[int] = []
    ends: Dict[int, int] = {}
    for first, second in zip(document.sentences, document.sentences[1:]):
        if document.section_at(first.start) != document.section_at(second.start):
            continue
        if not first.text.rstrip().endswith("?"):
            continue
        if second.word_count > int(options.get("answer_max_words", 5)) or second.text.rstrip().endswith("?"):
            continue
        offsets.append(first.start)
        ends[first.start] = second.end
    max_occurrences = int(options.get("max", 1))
    window_words = int(options.get("window_words", 400))
    return [
        Finding(
            cluster[max_occurrences],
            ends.get(cluster[-1], cluster[-1] + 1),
            "{} staged question-and-short-answer turns appear within {} words.".format(len(cluster), window_words),
            "Turn at least one question into a direct statement.",
        )
        for cluster in cluster_offsets(document, offsets, max_occurrences=max_occurrences, window_words=window_words)
    ]

def check_question_density(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    questions = [sentence.start for sentence in document.sentences if sentence.text.rstrip().endswith("?")]
    max_occurrences = int(options.get("max", 3))
    window_words = int(options.get("window_words", 500))
    return [
        Finding(
            cluster[max_occurrences],
            cluster[-1] + 1,
            "{} questions appear within {} words; the passage is interrogating the reader instead of explaining.".format(
                len(cluster), window_words
            ),
            "Keep the question that creates useful tension and state the others directly.",
        )
        for cluster in cluster_offsets(document, questions, max_occurrences=max_occurrences, window_words=window_words)
    ]

def check_echoed_clauses(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    minimum_clauses = int(options.get("minimum_clauses", 3))
    maximum_clauses = int(options.get("maximum_clauses", 5))
    findings: List[Finding] = []
    for sentence in document.sentences:
        raw = document.structural[sentence.start:sentence.end]
        pieces = [normalize_space(piece) for piece in re.split(r"\s*(?:,|;)\s*(?:(?:and|or)\s+)?", raw)]
        pieces = [piece for piece in pieces if len(WORD_RE.findall(piece)) >= 3]
        if not minimum_clauses <= len(pieces) <= maximum_clauses:
            continue
        if sum(bool(re.search(r"\d", piece)) for piece in pieces) >= max(2, len(pieces) // 2):
            continue
        prefixes: Dict[str, int] = {}
        suffixes: Dict[str, int] = {}
        for piece in pieces:
            words = [match.group(0).lower() for match in WORD_RE.finditer(piece)]
            if len(words) < 3:
                continue
            prefixes[" ".join(words[:2])] = prefixes.get(" ".join(words[:2]), 0) + 1
            suffixes[" ".join(words[-2:])] = suffixes.get(" ".join(words[-2:]), 0) + 1
        repeated_prefix = next((key for key, count in prefixes.items() if count >= minimum_clauses), None)
        repeated_suffix = next((key for key, count in suffixes.items() if count >= minimum_clauses), None)
        if repeated_prefix or repeated_suffix:
            repeated = repeated_prefix or repeated_suffix
            if re.search(r"\d", repeated):
                continue
            position = "opening" if repeated_prefix else "ending"
            findings.append(
                Finding(
                    sentence.start,
                    sentence.end,
                    "{} parallel clauses repeat the {} '{}'.".format(len(pieces), position, repeated),
                    "Keep the parallelism only if the rhythm earns its space; otherwise combine the clauses or vary the syntax.",
                )
            )
    return findings

def check_tricolon_density(document: Document, options: Mapping[str, Any]) -> List[Finding]:
    spans: List[Span] = []
    colon_pattern = re.compile(
        r":\s*[^,.;!?\n]{1,36},\s*[^,.;!?\n]{1,36},\s*(?:and|or)\s+[^.;!?\n]{1,48}",
        re.IGNORECASE,
    )
    gerund_pattern = re.compile(
        r"\b[A-Za-z]+ing\s+[^,.;!?\n]{0,30},\s*[A-Za-z]+ing\s+[^,.;!?\n]{0,30},\s*(?:and|or)\s+[A-Za-z]+ing\b",
        re.IGNORECASE,
    )
    spans.extend(Span(match.start(), match.end()) for match in colon_pattern.finditer(document.structural))
    spans.extend(Span(match.start(), match.end()) for match in gerund_pattern.finditer(document.structural))

    # Catch ordinary Oxford-comma triads, but count at most one per sentence. The
    # density threshold keeps a normal list from becoming a style violation.
    for sentence in document.sentences:
        raw = document.structural[sentence.start:sentence.end]
        if raw.count(",") != 2 or not re.search(r",\s*(?:and|or)\s+", raw, re.IGNORECASE):
            continue
        parts = [normalize_space(part) for part in re.split(r",\s*(?:and|or\s+)?|\s+(?:and|or)\s+", raw)]
        parts = [part for part in parts if part]
        if len(parts) == 3 and all(1 <= len(WORD_RE.findall(part)) <= 8 for part in parts):
            spans.append(Span(sentence.start, sentence.end))

    spans = dedupe_overlapping(spans)
    max_occurrences = int(options.get("max", 3))
    window_words = int(options.get("window_words", 750))
    return [
        Finding(
            cluster[max_occurrences],
            next((span.end for span in spans if span.start == cluster[-1]), cluster[-1] + 1),
            "{} three-part rhetorical lists appear within {} words.".format(len(cluster), window_words),
            "Vary the list length or convert one list into a concrete example.",
        )
        for cluster in cluster_offsets(document, [span.start for span in spans], max_occurrences=max_occurrences, window_words=window_words)
    ]
