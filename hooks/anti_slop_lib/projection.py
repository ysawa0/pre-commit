"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import List, Optional, Set

from .model import Span
from .text import line_spans

HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+|$)")

LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")

BLOCKQUOTE_RE = re.compile(r"^ {0,3}>")

REFERENCE_DEF_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*\S+")

THEMATIC_RE = re.compile(r"^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")

TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")

class Projection:
    """Offset-preserving views of Markdown source."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.visible = list(source)
        self.structural = list(source)
        self.line_spans = line_spans(source)
        self.heading_spans: List[Span] = []
        self.bold_spans: List[Span] = []
        self.parenthetical_spans: List[Span] = []
        self._project()

    def mask(self, start: int, end: int, *, visible: bool = True, structural: bool = True) -> None:
        targets: List[List[str]] = []
        if visible:
            targets.append(self.visible)
        if structural:
            targets.append(self.structural)
        for target in targets:
            for index in range(max(0, start), min(len(target), end)):
                if target[index] not in "\r\n":
                    target[index] = " "

    def _line_was_masked(self, start: int, end: int) -> bool:
        """Return true when an earlier projection pass hid a nonblank line."""
        return bool(self.source[start:end].strip()) and not any(
            not char.isspace() for char in self.visible[start:end]
        )

    def _project(self) -> None:
        self._mask_front_matter()
        self._mask_fenced_code()
        self._mask_html_comments()
        self._mask_line_constructs()
        self._mask_inline_constructs()
        visible = "".join(self.visible)
        self.bold_spans = [
            Span(match.start(), match.end())
            for match in re.finditer(r"(?<!\\)(\*\*|__)(?=\S)(.+?)(?<=\S)\1", visible, re.DOTALL)
            if "\n\n" not in match.group(0)
        ]
        self.parenthetical_spans = [
            Span(match.start(), match.end())
            for match in re.finditer(r"\([^()\n]{2,120}\)", visible)
        ]
        self._mask_markdown_punctuation()

    def _mask_front_matter(self) -> None:
        if not self.line_spans:
            return
        first_start, first_end = self.line_spans[0]
        first = self.source[first_start:first_end].strip()
        if first != "---":
            return
        for index in range(1, min(len(self.line_spans), 200)):
            start, end = self.line_spans[index]
            if self.source[start:end].strip() in {"---", "..."}:
                self.mask(first_start, end)
                return

    def _mask_fenced_code(self) -> None:
        open_char: Optional[str] = None
        open_len = 0
        block_start = 0
        for start, end in self.line_spans:
            line = self.source[start:end]
            match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if open_char is None:
                if match:
                    marker = match.group(1)
                    open_char = marker[0]
                    open_len = len(marker)
                    block_start = start
            else:
                if re.match(r"^ {0,3}" + re.escape(open_char) + "{" + str(open_len) + r",}\s*$", line):
                    self.mask(block_start, end)
                    open_char = None
                    open_len = 0
        if open_char is not None:
            self.mask(block_start, len(self.source))

    def _mask_html_comments(self) -> None:
        for match in re.finditer(r"<!--[\s\S]*?-->", self.source):
            self.mask(match.start(), match.end())
        for match in re.finditer(
            r"<(pre|script|style|code)\b[^>]*>[\s\S]*?</\1\s*>",
            self.source,
            re.IGNORECASE,
        ):
            self.mask(match.start(), match.end())

    def _mask_line_constructs(self) -> None:
        table_lines: Set[int] = set()
        list_lines: Set[int] = set()
        active_list_indent: Optional[int] = None
        for index, (start, end) in enumerate(self.line_spans):
            line = self.source[start:end]
            if self._line_was_masked(start, end):
                active_list_indent = None
                continue
            marker = LIST_RE.match(line)
            if marker:
                list_lines.add(index)
                active_list_indent = marker.end()
                continue
            if active_list_indent is not None:
                if not line.strip():
                    active_list_indent = None
                else:
                    indent = len(line) - len(line.lstrip(" "))
                    if indent >= active_list_indent:
                        list_lines.add(index)
                    else:
                        active_list_indent = None

        for index, (start, end) in enumerate(self.line_spans):
            line = self.source[start:end]
            if self._line_was_masked(start, end):
                continue
            if TABLE_SEPARATOR_RE.match(line):
                table_lines.add(index)
                if index > 0 and "|" in self.source[self.line_spans[index - 1][0] : self.line_spans[index - 1][1]]:
                    table_lines.add(index - 1)
                cursor = index + 1
                while cursor < len(self.line_spans):
                    cstart, cend = self.line_spans[cursor]
                    candidate = self.source[cstart:cend]
                    if not candidate.strip() or "|" not in candidate:
                        break
                    table_lines.add(cursor)
                    cursor += 1

        setext_title_lines: Set[int] = set()
        setext_underline_lines: Set[int] = set()
        for index in range(1, len(self.line_spans)):
            start, end = self.line_spans[index]
            line = self.source[start:end]
            if self._line_was_masked(start, end):
                continue
            if re.match(r"^ {0,3}(?:=+|-+)\s*$", line):
                pstart, pend = self.line_spans[index - 1]
                if self.source[pstart:pend].strip():
                    setext_title_lines.add(index - 1)
                    setext_underline_lines.add(index)
                    self.heading_spans.append(Span(pstart, pend))

        for index, (start, end) in enumerate(self.line_spans):
            line = self.source[start:end]
            if self._line_was_masked(start, end):
                continue
            if index in table_lines:
                self.mask(start, end)
                continue
            if index in setext_title_lines:
                # Keep heading words available to phrase rules, but exclude them
                # from sentence, paragraph, and rhythm analysis.
                self.mask(start, end, visible=False, structural=True)
                continue
            if index in setext_underline_lines:
                self.mask(start, end)
                continue
            if BLOCKQUOTE_RE.match(line):
                self.mask(start, end)
                continue
            if re.match(r"^(?: {4}|\t)", line) and index not in list_lines:
                self.mask(start, end)
                continue
            if re.match(r"^\s*(?:import|export)\s+", line):
                self.mask(start, end)
                continue
            if REFERENCE_DEF_RE.match(line) or THEMATIC_RE.match(line):
                self.mask(start, end)
                continue
            heading = HEADING_RE.match(line)
            if heading:
                self.heading_spans.append(Span(start, end))
                self.mask(start, end, visible=False, structural=True)
                self.mask(start, start + heading.end(), visible=True, structural=False)
                continue
            if index in list_lines:
                # Phrase-level rules still inspect list prose. Rhythm rules do not.
                self.mask(start, end, visible=False, structural=True)
                marker = LIST_RE.match(line)
                if marker:
                    self.mask(start, start + marker.end(), visible=True, structural=False)

    def _mask_inline_constructs(self) -> None:
        # Inline code spans, including variable-length backtick delimiters.
        index = 0
        while index < len(self.source):
            if self.source[index] != "`" or self.visible[index] == " ":
                index += 1
                continue
            run_end = index + 1
            while run_end < len(self.source) and self.source[run_end] == "`":
                run_end += 1
            marker = self.source[index:run_end]
            close = self.source.find(marker, run_end)
            if close == -1:
                index = run_end
                continue
            self.mask(index, close + len(marker))
            index = close + len(marker)

        # Images are not prose; link text is prose but destinations are not.
        for match in re.finditer(r"!\[[^\]]*\]\([^\n)]*\)", self.source):
            self.mask(match.start(), match.end())
        for match in re.finditer(r"(?<!!)\[[^\]\n]+\]\(([^\n)]*)\)", self.source):
            destination_start = match.start(1)
            self.mask(destination_start, match.end(1))
        for match in re.finditer(r"<(?:(?:https?|mailto):[^>]+)>", self.source, re.IGNORECASE):
            self.mask(match.start(), match.end())
        for match in re.finditer(r"\b(?:https?://|www\.)[^\s<>()]+", self.source, re.IGNORECASE):
            self.mask(match.start(), match.end())
        for match in re.finditer(r"</?[A-Za-z][^>\n]*>", self.source):
            self.mask(match.start(), match.end())

    def _mask_markdown_punctuation(self) -> None:
        for target in (self.visible, self.structural):
            for index, char in enumerate(target):
                if char in "*_`":
                    target[index] = " "
