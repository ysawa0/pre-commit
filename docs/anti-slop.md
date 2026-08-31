# anti-slop design and rule guide

`anti-slop` is a deterministic prose linter for Markdown and MDX. Its job is narrow: point to writing patterns that are canned, repetitive, bloated, or mechanically over-polished, then explain the complaint at the source location.

It is not an authorship detector. A human can write bland prose, a model can write clean prose, and punctuation is not biometric evidence. The tool evaluates the text in front of it.

## Design principles

### Flag accumulation, not personality

Most stylistic devices are legitimate in moderation. A single em dash, rhetorical question, three-part list, or contrast can help a passage. The default rules focus on clusters and density so the linter complains when a device becomes a habit.

### Prefer structure over word blacklists

The strongest rules look for repeated sentence openings, recurring paragraph moves, stacked question-and-answer turns, repeated contrast scaffolding, and parallel clauses. Loaded vocabulary matters mainly when the same word recurs within a short window.

### Explain every result

Each diagnostic contains a stable rule ID, severity, source range, explanation, and revision strategy. There is no opaque percentage or unsupported claim about who wrote the document.

### Keep CI tolerable

The recommended preset enables rules with a practical signal-to-noise ratio. More subjective rhythm checks are disabled or informational until the strict preset is selected. Local suppressions are part of the design rather than a reluctant escape hatch added after everyone becomes furious.

## Markdown projection

The parser creates two offset-preserving views of the document:

1. A visible-prose view for phrase and density rules.
2. A structural-prose view for sentence, paragraph, and rhythm rules.

Source offsets stay unchanged, which allows exact line and column diagnostics without a dependency-heavy syntax tree.

The following constructs are ignored by default:

- YAML front matter;
- fenced and indented code;
- inline code;
- HTML comments and raw `pre`, `code`, `script`, or `style` blocks;
- URLs and link destinations;
- images;
- reference definitions;
- blockquotes;
- Markdown tables;
- MDX import and export lines;
- MDX and HTML tags.

List prose remains available to phrase rules, but lists do not participate in rhythm analysis. Headings remain available to phrase rules, but every heading resets section-scoped repetition and staccato checks. This prevents repeated API-entry templates from producing a cloud of useless warnings.

## Presets and failure levels

`recommended` is the default. Warnings fail the command, informational findings do not, and errors always represent mechanical residue or a similarly objective defect.

`strict` promotes several subjective rules and enables document-level rhythm checks.

The independent `fail_level` setting accepts:

- `info`;
- `warning`;
- `error`;
- `none`.

This separation lets a team display style suggestions in CI without blocking a change.

## Rule catalog

| Rule | Recommended | What it catches |
| --- | --- | --- |
| `artifact.chatbot-residue` | error | Pasted generated-citation markers and chatbot boilerplate |
| `verbosity.throat-clearing` | warning | Generic openings that delay the actual claim |
| `verbosity.filler` | warning | Wordy phrases with direct replacements |
| `verbosity.redundant-pair` | warning | Doubled expressions such as `each and every` |
| `phrase.note-to-reader` | info | Editorial scaffolding that tells the reader what to notice |
| `phrase.marketing-language` | info | Promotional language without a concrete property |
| `phrase.abstract-role` | info | Ceremonial role language that hides a direct verb |
| `phrase.landscape` | warning | Vague landscape and tapestry metaphors |
| `phrase.vague-attribution` | warning | Claims assigned to unnamed experts or studies |
| `rhetoric.negative-parallelism` | warning | Repeated `not X, but Y` reframes within a word window |
| `rhetoric.no-chain` | warning | Three or more `no X, no Y` items in a chain |
| `rhetoric.question-answer` | warning | Repeated staged questions followed by tiny answers |
| `rhetoric.question-density` | warning | Too many questions in a short passage |
| `rhetoric.echoed-clauses` | warning | Parallel clauses with the same opening or ending |
| `rhetoric.tricolon-density` | info | Repeated three-part rhetorical lists |
| `repetition.sentence-opener` | warning | Repeated two-word sentence openings within one section |
| `repetition.paragraph-opener` | warning | Repeated two-word paragraph openings within one section |
| `repetition.transition` | warning | Stock transitions reused inside a short window |
| `repetition.loaded-word` | warning | Recurring abstract or promotional vocabulary |
| `rhythm.short-sentence-run` | warning | Three or more very short sentences in one section |
| `rhythm.uniform-sentence-length` | off | Unusually low sentence-length variation |
| `density.em-dash` | warning | More than four em dashes within 500 words |
| `density.bold` | warning | More than ten bold spans within 500 words |
| `density.parenthetical` | off | Many parenthetical asides within a short passage |
| `structure.heading-density` | off | Too many headings for the amount of prose |

Run `hooks/anti_slop.py --list-rules` to inspect the installed rule set and preset severities.

## Configuration

The linter reads `.anti-slop.json` from the current working directory unless `--config` names another file.

```json
{
  "preset": "recommended",
  "fail_level": "warning",
  "rules": {
    "rhetoric.negative-parallelism": {
      "severity": "warning",
      "max": 2,
      "window_words": 700
    },
    "density.em-dash": {
      "max": 6,
      "window_words": 1000
    },
    "phrase.marketing-language": "off"
  }
}
```

A string changes only the severity. An object can change severity and documented thresholds. Unknown rules, severities, and option names are configuration errors. A typo should not quietly disable enforcement.

## Suppressions

Disable a rule on the next source line:

```markdown
<!-- anti-slop-disable-next-line rhetoric.negative-parallelism -->
The quoted slogan is not a feature. It is a promise.
```

Disable one or more rule families for a region:

```markdown
<!-- anti-slop-disable rhetoric.* repetition.* -->
This passage intentionally uses anaphora.
<!-- anti-slop-enable rhetoric.* repetition.* -->
```

Ignore a result on the current line:

```markdown
The product name is “Ultimate Guide.” <!-- anti-slop-ignore phrase.marketing-language -->
```

An omitted selector means `all`.

## Output formats

Text output is intended for terminals and pre-commit:

```text
article.md:18:7: warning [repetition.sentence-opener] 4 sentences repeatedly open with 'the best'.
  suggestion: Merge a sentence or vary the grammatical opening unless the repetition is deliberate anaphora.
```

JSON output provides source ranges and suggestions for integrations. GitHub output emits workflow commands that appear as annotations on changed lines.

## Rule-development standard

A new rule should satisfy four tests:

1. It describes a writing problem rather than guessing authorship.
2. The result points to a specific editable passage.
3. A user can understand why it fired without reading the implementation.
4. It survives a calibration corpus of polished human prose and technical reference material.

Density rules should include both a maximum count and a word window. Structural rules should distinguish one deliberate use from a repeated habit. Phrase rules should offer a direct revision strategy.

## Known limits

The linter currently targets English prose. Its Markdown projection covers the constructs that create the largest false-positive risks, but it is not a complete CommonMark parser. Sentence splitting is deterministic and conservative rather than linguistically perfect. The tool does not rewrite subjective passages automatically because canned fixes are a rather efficient way to create a second generation of canned prose.

## Influences

The rule-selection process was informed by Simon Willison's LLM cliché highlighter, Wikipedia's guide to signs of machine-generated writing, `anti-slop`, `defluff`, and `slop-lint`. This implementation is independent, dependency-free, and organized around pre-commit diagnostics rather than authorship classification.
