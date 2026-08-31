import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "anti_slop.py"
FIXTURES = ROOT / "test" / "fixtures" / "anti_slop"
EXAMPLES = ROOT / "examples" / "anti-slop"

spec = importlib.util.spec_from_file_location("anti_slop", str(HOOK))
anti_slop = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = anti_slop
spec.loader.exec_module(anti_slop)


class AntiSlopTest(unittest.TestCase):
    def lint_text(self, text, preset="recommended", config=None):
        document = anti_slop.Document("test.md", text)
        return anti_slop.lint_document(document, preset, config or {})

    def test_coffee_before_exercises_high_value_rules(self):
        text = (EXAMPLES / "coffee-before.md").read_text(encoding="utf-8")
        diagnostics = self.lint_text(text)
        rule_ids = {item.rule_id for item in diagnostics}
        self.assertGreaterEqual(len(diagnostics), 30)
        self.assertTrue(
            {
                "rhetoric.negative-parallelism",
                "rhetoric.no-chain",
                "rhetoric.question-answer",
                "rhetoric.question-density",
                "repetition.sentence-opener",
                "repetition.loaded-word",
                "rhythm.short-sentence-run",
                "density.em-dash",
                "verbosity.filler",
            }.issubset(rule_ids)
        )

    def test_revised_coffee_article_is_clean(self):
        text = (EXAMPLES / "coffee-after.md").read_text(encoding="utf-8")
        self.assertEqual(self.lint_text(text), [])

    def test_markdown_projection_ignores_non_prose(self):
        text = """---
title: In today's ever-evolving landscape
---

> In order to unlock the power of coffee.

`In order to unlock the power of coffee.`

[clean link](https://example.com/?utm_source=chatgpt)

```text
In order to unlock the power of coffee.
turn1search2
```

<!-- In order to unlock the power of coffee. -->

A plain, direct sentence remains.
"""
        self.assertEqual(self.lint_text(text), [])

    def test_mdx_tags_are_masked_but_text_is_linted(self):
        diagnostics = self.lint_text("<Callout>In order to make coffee, weigh it.</Callout>\n")
        self.assertEqual([item.rule_id for item in diagnostics], ["verbosity.filler"])
        self.assertEqual(diagnostics[0].line, 1)

    def test_code_blocks_and_mdx_imports_are_not_prose(self):
        text = """import Callout from './Callout.js'

    In order to unlock the power of coffee.

<pre>
In order to unlock the power of coffee.
</pre>

A direct sentence remains.
"""
        self.assertEqual(self.lint_text(text), [])

    def test_setext_heading_is_visible_to_phrase_rules_not_rhythm_rules(self):
        diagnostics = self.lint_text("The Ultimate Guide\n==================\n\nCoffee tastes good.\n")
        self.assertEqual([item.rule_id for item in diagnostics], ["phrase.marketing-language"])
        self.assertEqual(diagnostics[0].line, 1)

    def test_overlapping_phrase_patterns_report_once(self):
        diagnostics = self.lint_text("In today's ever-evolving coffee landscape, choice can be difficult.\n")
        landscape = [item for item in diagnostics if item.rule_id == "phrase.landscape"]
        self.assertEqual(len(landscape), 1)

    def test_chatbot_residue_is_an_error(self):
        diagnostics = self.lint_text("The draft still contains turn4search12 in the paragraph.\n")
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].rule_id, "artifact.chatbot-residue")
        self.assertEqual(diagnostics[0].severity, "error")

    def test_negative_parallelism_is_density_based(self):
        one = "This is not a speed problem. It is a coordination problem.\n"
        self.assertNotIn("rhetoric.negative-parallelism", {d.rule_id for d in self.lint_text(one)})

        two = one + "The failure is not about throughput, but predictability.\n"
        self.assertIn("rhetoric.negative-parallelism", {d.rule_id for d in self.lint_text(two)})

    def test_disable_next_line_suppresses_one_rule(self):
        text = """<!-- anti-slop-disable-next-line verbosity.filler -->
In order to weigh the coffee, use a scale.

In order to heat the water, use a kettle.
"""
        diagnostics = self.lint_text(text)
        fillers = [item for item in diagnostics if item.rule_id == "verbosity.filler"]
        self.assertEqual(len(fillers), 1)
        self.assertEqual(fillers[0].line, 4)

    def test_category_suppression_and_enable(self):
        text = """<!-- anti-slop-disable verbosity.* -->
In order to brew, use water.
<!-- anti-slop-enable verbosity.* -->
In order to brew, use water.
"""
        diagnostics = self.lint_text(text)
        fillers = [item for item in diagnostics if item.rule_id == "verbosity.filler"]
        self.assertEqual(len(fillers), 1)
        self.assertEqual(fillers[0].line, 4)

    def test_inline_ignore_suppresses_selected_rule(self):
        text = "In order to brew, weigh the coffee. <!-- anti-slop-ignore verbosity.filler -->\n"
        self.assertEqual(self.lint_text(text), [])

    def test_repeated_sentence_openers_report_source_location(self):
        text = "Coffee tastes sweet. Coffee tastes bright. Coffee tastes clean.\n"
        diagnostics = [d for d in self.lint_text(text) if d.rule_id == "repetition.sentence-opener"]
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].line, 1)
        self.assertGreater(diagnostics[0].column, 1)

    def test_headings_reset_opener_and_short_sentence_runs(self):
        text = """# API

## Open

The event fires when the socket opens. Ready. Connected.

## Close

The event fires when the socket closes. Done. Disconnected.

## Error

The event fires when the socket fails. Failed. Closed.
"""
        rule_ids = {item.rule_id for item in self.lint_text(text)}
        self.assertNotIn("repetition.sentence-opener", rule_ids)
        self.assertNotIn("repetition.paragraph-opener", rule_ids)
        self.assertNotIn("rhythm.short-sentence-run", rule_ids)

    def test_heading_inside_code_does_not_reset_prose_section(self):
        text = """Coffee tastes sweet. Coffee tastes bright.

```markdown
# Not a real heading
```

Coffee tastes remarkably clean.
"""
        rule_ids = {item.rule_id for item in self.lint_text(text)}
        self.assertIn("repetition.sentence-opener", rule_ids)

    def test_single_em_dash_is_not_a_violation(self):
        self.assertEqual(self.lint_text("A grinder matters—but it need not be expensive.\n"), [])

    def test_strict_preset_enables_note_to_reader_as_warning(self):
        diagnostics = self.lint_text("It is important to note that water matters.\n", preset="strict")
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].severity, "warning")

    def test_rule_override_can_disable_a_rule(self):
        config = {"rules": {"verbosity.filler": "off"}}
        self.assertEqual(self.lint_text("In order to brew, use water.\n", config=config), [])

    def test_cli_json_and_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text("In order to brew, use water.\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(HOOK), "--format", "json", str(path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload[0]["rule"], "verbosity.filler")
            self.assertEqual(payload[0]["line"], 1)

    def test_cli_fail_level_error_allows_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text("In order to brew, use water.\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(HOOK), "--fail-level", "error", str(path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("verbosity.filler", result.stdout)

    def test_unknown_rule_in_config_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps({"rules": {"made.up": "off"}}), encoding="utf-8")
            with self.assertRaises(anti_slop.ConfigError):
                anti_slop.load_config(str(config_path))

    def test_unknown_rule_option_is_an_error(self):
        config = {"rules": {"density.em-dash": {"maximum": 3}}}
        document = anti_slop.Document("test.md", "One sentence.\n")
        with self.assertRaises(anti_slop.ConfigError):
            anti_slop.lint_document(document, "recommended", config)

    def test_invalid_option_range_is_an_error(self):
        config = {"rules": {"density.em-dash": {"max": -1}}}
        document = anti_slop.Document("test.md", "One sentence.\n")
        with self.assertRaises(anti_slop.ConfigError):
            anti_slop.lint_document(document, "recommended", config)

    def test_invalid_top_level_config_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps({"preset": ["strict"]}), encoding="utf-8")
            with self.assertRaises(anti_slop.ConfigError):
                anti_slop.load_config(str(config_path))


if __name__ == "__main__":
    unittest.main()
