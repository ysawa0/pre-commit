"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import bisect
from typing import List, Optional, Sequence, Tuple

from .model import Span, TextUnit
from .projection import Projection
from .suppressions import parse_suppressions, rule_selector_matches
from .text import compute_line_starts, extract_paragraphs, extract_words, split_sentences

class Document:
    def __init__(self, path: str, source: str) -> None:
        self.path = path
        self.source = source
        self.line_starts = compute_line_starts(source)
        self.suppressed_all, self.suppressed_rules = parse_suppressions(source)
        projection = Projection(source)
        self.visible = "".join(projection.visible)
        self.structural = "".join(projection.structural)
        self.heading_spans = sorted(projection.heading_spans, key=lambda span: span.start)
        self.heading_starts = [span.start for span in self.heading_spans]
        self.bold_spans = [span for span in projection.bold_spans if self._span_visible(span)]
        self.parenthetical_spans = [span for span in projection.parenthetical_spans if self._span_visible(span)]
        self.words = extract_words(self.visible)
        self.word_starts = [word.start for word in self.words]
        self.paragraphs = extract_paragraphs(self.structural)
        self.sentences: List[TextUnit] = []
        for paragraph in self.paragraphs:
            self.sentences.extend(split_sentences(paragraph.text, paragraph.start))

    def _span_visible(self, span: Span) -> bool:
        return any(not char.isspace() for char in self.visible[span.start:span.end])

    @property
    def word_count(self) -> int:
        return len(self.words)

    def word_index_at(self, offset: int) -> int:
        if not self.words:
            return 0
        index = bisect.bisect_right(self.word_starts, offset) - 1
        return max(0, index)

    def location(self, offset: int) -> Tuple[int, int]:
        line_index = bisect.bisect_right(self.line_starts, offset) - 1
        line_index = max(0, line_index)
        return line_index + 1, offset - self.line_starts[line_index] + 1

    def section_at(self, offset: int) -> int:
        """Return the Markdown heading section containing an offset.

        Every heading starts a new comparison section. Repetition across sibling
        API entries, FAQ questions, or similarly templated reference sections is
        usually useful structure, not monotonous prose.
        """
        return bisect.bisect_right(self.heading_starts, offset)

    def units_by_section(self, units: Sequence[TextUnit]) -> List[List[TextUnit]]:
        groups: List[List[TextUnit]] = []
        current_section: Optional[int] = None
        for unit in units:
            section = self.section_at(unit.start)
            if section != current_section:
                groups.append([])
                current_section = section
            groups[-1].append(unit)
        return groups

    def is_suppressed(self, offset: int, rule_id: str) -> bool:
        line_index = bisect.bisect_right(self.line_starts, offset) - 1
        line_index = min(max(0, line_index), len(self.suppressed_all) - 1)
        if self.suppressed_all[line_index]:
            return True
        return any(rule_selector_matches(selector, rule_id) for selector in self.suppressed_rules[line_index])

    def excerpt(self, line: int) -> str:
        lines = self.source.splitlines()
        if 1 <= line <= len(lines):
            return lines[line - 1]
        return ""
