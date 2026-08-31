"""Internal implementation for the anti-slop Markdown prose linter."""

from __future__ import annotations

from typing import List

from ..model import Rule
from ..rule_utils import make_phrase_rule


def rules() -> List[Rule]:
    return [
        Rule(
                    "phrase.marketing-language",
                    "Generic promotional wording without a concrete property",
                    "info",
                    make_phrase_rule(
                        [
                            (r"\bunlock(?:s|ed|ing)? (?:the )?(?:power|potential|possibilities)\b", "'Unlocking potential' is promotional unless the mechanism is named.", "Describe the capability or measured result."),
                            (r"\bseamless(?:ly)?\b", "'Seamless' makes a quality claim without naming the seam.", "Name the transition, integration, or failure mode."),
                            (r"\bgame[- ]changer\b", "'Game-changer' substitutes enthusiasm for evidence.", "Describe what changed and by how much."),
                            (r"\belevat(?:e|es|ed|ing) (?:your|the)\b", "'Elevate' is generic promotional language here.", "Use the concrete improvement."),
                            (r"\btransformative\b", "'Transformative' needs a specific before-and-after claim.", "Describe the transformation."),
                            (r"\bultimate guide\b", "'Ultimate guide' makes a completeness claim the article is unlikely to prove.", "Use a descriptive title that states the scope."),
                        ]
                    ),
                    strict_severity="warning",
                ),
        Rule(
                    "phrase.abstract-role",
                    "Abstract role language that can usually be replaced by a direct verb",
                    "info",
                    make_phrase_rule(
                        [
                            (r"\bserves as (?:a|an|the)\b", "'Serves as' often hides a simpler verb.", "Use 'is', 'provides', or the specific action."),
                            (r"\bplays? (?:a )?(?:pivotal|crucial|vital|important) role\b", "The sentence announces importance without demonstrating it.", "Name the consequence or dependency."),
                            (r"\bstands as (?:a|an|the)\b", "'Stands as' adds ceremony to a direct claim.", "Use 'is' or a more specific verb."),
                        ]
                    ),
                    strict_severity="warning",
                ),
        Rule(
                    "phrase.landscape",
                    "Vague landscape or tapestry metaphors",
                    "warning",
                    make_phrase_rule(
                        [
                            (r"\bever[- ]evolving(?:\s+[A-Za-z-]+){0,2}\s+landscape\b", "'Ever-evolving landscape' is vague and overworked.", "Name what changed and when."),
                            (r"\bin today['’]s(?:\s+[A-Za-z-]+){0,2}\s+landscape\b", "The 'today's ... landscape' frame is generic.", "Name the current condition and its date or consequence."),
                            (r"\b(?:rich|complex|intricate) tapestry\b", "The tapestry metaphor decorates the claim without clarifying it.", "Describe the actual components or relationship."),
                        ]
                    ),
                ),
        Rule(
                    "phrase.vague-attribution",
                    "Claims attributed to unnamed authorities",
                    "warning",
                    make_phrase_rule(
                        [
                            (r"\bexperts (?:say|argue|believe|agree)\b", "'Experts' is too vague to support the claim.", "Name the expert, institution, or source."),
                            (r"\bstudies (?:show|suggest|indicate|have shown)\b", "'Studies' needs a citation or identifying detail.", "Cite the study or state what evidence you reviewed."),
                            (r"\bit is widely (?:believed|known|accepted)\b", "A claim of broad agreement needs evidence.", "Name the source of the consensus or remove the appeal to consensus."),
                        ]
                    ),
                ),
    ]
