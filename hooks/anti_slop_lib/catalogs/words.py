"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import List

from ..checks.artifact import check_chatbot_residue
from ..model import Rule
from ..rule_utils import make_phrase_rule


def rules() -> List[Rule]:
    return [
        Rule(
                    "artifact.chatbot-residue",
                    "Generated-chat or citation artifacts left in prose",
                    "error",
                    check_chatbot_residue,
                ),
        Rule(
                    "verbosity.throat-clearing",
                    "Generic opening clauses that delay the actual claim",
                    "warning",
                    make_phrase_rule(
                        [
                            (r"\bwhen it comes to\b", "'When it comes to' delays the subject.", "Start with the subject and verb."),
                            (r"\bin (?:today's|the modern|an? ever-changing|an? ever-evolving) (?:world|era|landscape)\b", "A generic era/landscape opener adds atmosphere instead of information.", "Name the specific change, market, or constraint."),
                            (r"\bin the (?:realm|world) of\b", "'In the realm/world of' is a vague throat-clearing phrase.", "Name the field directly."),
                            (r"\bat its core\b", "'At its core' often announces a simplification instead of making it.", "State the simplified claim directly."),
                            (r"\bthe fact of the matter is\b", "'The fact of the matter is' delays the claim.", "Delete the lead-in."),
                            (r"\bit goes without saying\b|\bneedless to say\b", "If it goes without saying, it probably should not occupy the sentence.", "Delete the phrase or supply the missing evidence."),
                            (r"\bas we navigate\b", "'As we navigate' creates generic motion without identifying an action.", "Name who is doing what."),
                        ]
                    ),
                ),
        Rule(
                    "verbosity.filler",
                    "Wordy phrases with shorter direct equivalents",
                    "warning",
                    make_phrase_rule(
                        [
                            (r"\bin order to\b", "'In order to' is usually just 'to'.", "Replace it with 'to'."),
                            (r"\bdue to the fact that\b", "'Due to the fact that' is wordier than 'because'.", "Replace it with 'because'."),
                            (r"\bat this point in time\b", "'At this point in time' is usually just 'now'.", "Replace it with 'now'."),
                            (r"\bhas the ability to\b|\bis able to\b", "This ability phrase usually hides a direct verb.", "Use 'can' or the direct verb."),
                            (r"\bfor the purpose of\b", "'For the purpose of' is needlessly long.", "Use 'for' or 'to'."),
                            (r"\ba (?:large|significant) number of\b", "This quantity phrase is vague and wordy.", "Use 'many' or provide the number."),
                            (r"\ba wide variety of\b", "'A wide variety of' is vague unless the variety matters.", "Use 'many', list examples, or quantify."),
                            (r"\bin the event that\b", "'In the event that' is usually just 'if'.", "Replace it with 'if'."),
                            (r"\bwith regard to\b", "'With regard to' is usually unnecessary.", "Use 'about' or begin with the subject."),
                        ]
                    ),
                ),
        Rule(
                    "verbosity.redundant-pair",
                    "Redundant or doubled expressions",
                    "warning",
                    make_phrase_rule(
                        [
                            (r"\beach and every\b", "'Each and every' repeats the same idea.", "Choose 'each' or 'every'."),
                            (r"\bvarious different\b", "'Various different' is redundant.", "Choose 'various' or 'different'."),
                            (r"\bpast history\b", "History is already in the past.", "Use 'history'."),
                            (r"\bfuture plans\b", "Plans normally concern the future.", "Use 'plans' unless contrasting with past plans."),
                            (r"\bend result\b", "A result is already an end state.", "Use 'result'."),
                            (r"\bcompletely eliminate\b", "'Eliminate' already means remove completely.", "Use 'eliminate'."),
                            (r"\bmay possibly\b|\bcould potentially\b", "Stacked hedges weaken the sentence twice.", "Keep one hedge."),
                        ]
                    ),
                ),
        Rule(
                    "phrase.note-to-reader",
                    "Meta-language that tells the reader what to notice",
                    "info",
                    make_phrase_rule(
                        [
                            (r"\bit (?:is|'s) important to note that\b", "The sentence tells the reader to note a claim instead of proving its importance.", "Delete the lead-in and strengthen the claim."),
                            (r"\bit (?:is|'s) worth noting that\b|\bit should be noted that\b", "The note-to-reader phrase adds editorial scaffolding.", "State the point directly."),
                            (r"\bthe key takeaway is\b", "'The key takeaway is' often repeats a point the paragraph should already establish.", "State the takeaway once, in the strongest location."),
                        ]
                    ),
                    strict_severity="warning",
                ),
    ]
