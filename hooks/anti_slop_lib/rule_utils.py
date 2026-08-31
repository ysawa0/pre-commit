"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple

from .document import Document
from .model import Finding

def cluster_offsets(
    document: Document,
    offsets: Sequence[int],
    *,
    max_occurrences: int,
    window_words: int,
) -> List[List[int]]:
    if len(offsets) <= max_occurrences:
        return []
    ordered = sorted(set(offsets))
    word_indices = [document.word_index_at(offset) for offset in ordered]
    clusters: List[List[int]] = []
    left = 0
    right = 0
    while right < len(ordered):
        while word_indices[right] - word_indices[left] > window_words:
            left += 1
        if right - left + 1 > max_occurrences:
            cluster = ordered[left : right + 1]
            # Extend to include subsequent occurrences still in the same window.
            cursor = right + 1
            while cursor < len(ordered) and word_indices[cursor] - word_indices[left] <= window_words:
                cluster.append(ordered[cursor])
                cursor += 1
            clusters.append(cluster)
            right = cursor
            left = right
        else:
            right += 1
    return clusters

def regex_findings(
    document: Document,
    patterns: Sequence[Tuple[re.Pattern[str], str, Optional[str]]],
) -> List[Finding]:
    candidates: List[Finding] = []
    for pattern, message, suggestion in patterns:
        for match in pattern.finditer(document.visible):
            candidates.append(Finding(match.start(), match.end(), message.format(match=match.group(0)), suggestion))

    # A broad phrase and a nested phrase can both match the same words. Report
    # the broadest explanation once instead of nagging twice at one sentence.
    findings: List[Finding] = []
    for finding in sorted(candidates, key=lambda item: (item.start, -(item.end - item.start))):
        if any(finding.start < existing.end and existing.start < finding.end for existing in findings):
            continue
        findings.append(finding)
    return sorted(findings, key=lambda item: item.start)

def make_phrase_rule(
    entries: Sequence[Tuple[str, str, Optional[str]]],
    flags: int = re.IGNORECASE,
) -> Callable[[Document, Mapping[str, Any]], List[Finding]]:
    compiled = [(re.compile(pattern, flags), message, suggestion) for pattern, message, suggestion in entries]

    def check(document: Document, _: Mapping[str, Any]) -> List[Finding]:
        return regex_findings(document, compiled)

    return check
