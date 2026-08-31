"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

from .model import Span, TextUnit, Word, WORD_RE

def line_spans(source: str) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    start = 0
    for match in re.finditer(r"\r?\n", source):
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(source)))
    return spans

def compute_line_starts(source: str) -> List[int]:
    starts = [0]
    starts.extend(match.end() for match in re.finditer(r"\n", source))
    return starts

def extract_words(text: str) -> List[Word]:
    return [
        Word(match.group(0), match.group(0).lower().replace("’", "'"), match.start(), match.end())
        for match in WORD_RE.finditer(text)
    ]

def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def extract_paragraphs(structural: str) -> List[TextUnit]:
    paragraphs: List[TextUnit] = []
    current_start: Optional[int] = None
    current_end = 0
    for start, end in line_spans(structural):
        line = structural[start:end]
        if line.strip():
            if current_start is None:
                current_start = start
            current_end = end
        elif current_start is not None:
            text = structural[current_start:current_end]
            word_count = len(WORD_RE.findall(text))
            if text.strip() and word_count >= 4:
                paragraphs.append(TextUnit(current_start, current_end, text, word_count))
            current_start = None
    if current_start is not None:
        text = structural[current_start:current_end]
        word_count = len(WORD_RE.findall(text))
        if text.strip() and word_count >= 4:
            paragraphs.append(TextUnit(current_start, current_end, text, word_count))
    return paragraphs

ABBREVIATIONS = {
    "e.g.",
    "i.e.",
    "etc.",
    "vs.",
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "sr.",
    "jr.",
    "st.",
    "fig.",
    "no.",
}

def _looks_like_abbreviation(text: str, punctuation_index: int) -> bool:
    prefix = text[max(0, punctuation_index - 12) : punctuation_index + 1].lower()
    if any(prefix.endswith(item) for item in ABBREVIATIONS):
        return True
    token_match = re.search(r"\b([A-Za-z])\.$", prefix)
    return bool(token_match)

def split_sentences(text: str, base_offset: int) -> List[TextUnit]:
    units: List[TextUnit] = []
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        boundary = False
        if char in "!?":
            boundary = True
        elif char == "." and not _looks_like_abbreviation(text, index):
            boundary = True
        if not boundary:
            index += 1
            continue

        end = index + 1
        while end < len(text) and text[end] in ".!?\"'”’)]":
            end += 1
        if end < len(text) and not text[end].isspace():
            index += 1
            continue
        chunk = text[start:end]
        leading = len(chunk) - len(chunk.lstrip())
        trailing = len(chunk.rstrip())
        if trailing > leading:
            clean = normalize_space(chunk[leading:trailing])
            count = len(WORD_RE.findall(clean))
            if count:
                units.append(TextUnit(base_offset + start + leading, base_offset + start + trailing, clean, count))
        start = end
        index = end

    # Unterminated tails are common in API labels, definition lists, and headings.
    # Phrase rules still inspect them, but rhythm rules need an actual sentence.
    return units

def dedupe_overlapping(spans: Sequence[Span]) -> List[Span]:
    result: List[Span] = []
    for span in sorted(spans, key=lambda item: (item.start, -(item.end - item.start))):
        if any(span.start < existing.end and existing.start < span.end for existing in result):
            continue
        result.append(span)
    return sorted(result, key=lambda item: item.start)
