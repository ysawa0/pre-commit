# Coffee article calibration

This directory records the end-to-end calibration exercise used for `anti-slop` 0.2.0.

- [`coffee-before.md`](coffee-before.md) is intentionally padded with canned phrasing, repeated rhetorical shapes, promotional adjectives, and formatting habits.
- [`coffee-after.md`](coffee-after.md) answers the same practical questions directly and cites the Specialty Coffee Association for the brewing ratio, temperature range, equipment certification, and freshness material.

## Result

The final recommended preset reports:

| Document | Diagnostics | Warning | Info | Distinct rules |
| --- | ---: | ---: | ---: | ---: |
| `coffee-before.md` | 44 | 27 | 17 | 17 |
| `coffee-after.md` | 0 | 0 | 0 | 0 |

Reproduce the run:

```console
hooks/anti_slop.py --format json --fail-level none examples/anti-slop/coffee-before.md
hooks/anti_slop.py --format json --fail-level none examples/anti-slop/coffee-after.md
```

The noisy draft exercises high-value structural rules, including repeated sentence openings, negative parallelism, question-and-answer staging, question density, short-sentence runs, echoed clauses, three-part-list density, loaded-word repetition, and em-dash density. Phrase rules add precise cleanup suggestions rather than trying to infer authorship.

## Iterations made from the run

The first draft of the linter missed parallel clauses such as `the origin is crucial, the roast is crucial, and the freshness is crucial` That observation produced `rhetoric.echoed-clauses`.

Calibration against technical documentation exposed a false positive in API references: descriptions under separate headings often begin with the same template. Sentence and paragraph opening checks now reset at every heading. The change reduced noVNC's API guide from six repetition warnings to zero while retaining every expected coffee diagnostic.

Overlapping phrase patterns originally produced two complaints for one “today's ever-evolving ... landscape” phrase. Phrase findings are now deduplicated by source span.

The final version was also checked against these established documentation snapshots:

| Corpus | Revision | Result |
| --- | --- | ---: |
| noVNC `README.md` | `7fcf9dcfe0cc5b14e3841a4429dc091a6ffca861` | 0 |
| noVNC `docs/EMBEDDING.md` | same revision | 0 |
| noVNC `docs/API.md` | same revision | 0 |
| nvm `CONTRIBUTING.md` | `977563e97ddc66facf3a8e31c6cff01d236f09bd` | 1 |
| nvm `GOVERNANCE.md` | same revision | 0 |
| nvm `README.md` | same revision | 3 |

The four nvm findings are literal uses of `in order to`, the kind of direct, low-severity edit the rule is meant to surface. The calibration goal is not universal silence. It is a small set of understandable results that a writer can accept or suppress.
