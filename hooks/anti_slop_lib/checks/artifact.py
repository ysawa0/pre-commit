"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

import re
from typing import Any, List, Mapping

from ..document import Document
from ..model import Finding

def check_chatbot_residue(document: Document, _: Mapping[str, Any]) -> List[Finding]:
    pattern = re.compile(
        r"\bas an AI(?: language)? model\b|\bknowledge cutoff\b|\bas of my last (?:update|training)\b|"
        r"\bI (?:cannot|can't|do not|don't) (?:browse the internet|access real[- ]time)\b|"
        r"\boaicite\b|\bcontentReference\b|\battributableIndex\b|\bturn\d+(?:search|news|image|view)\d+\b|"
        r"[?&]utm_source=(?:chatgpt|openai)\b",
        re.IGNORECASE,
    )
    return [
        Finding(match.start(), match.end(), "Chatbot or generated-citation residue remains in the prose.", "Remove the artifact and verify the surrounding claim.")
        for match in pattern.finditer(document.visible)
    ]
