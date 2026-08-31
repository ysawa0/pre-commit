# Pre-commit hooks

This repository provides reusable hooks for [pre-commit](https://pre-commit.com/). It includes infrastructure checks inherited from the original Gruntwork hook collection and `anti-slop`, a deterministic Markdown prose linter.

## anti-slop

`anti-slop` catches writing that becomes distracting through repetition, vague filler, canned rhetoric, or excessive formatting. It does not estimate whether a person or a model wrote the text.

The hook is:

- deterministic and explainable;
- dependency-free on Python 3;
- aware of Markdown and MDX structure;
- conservative about one-off stylistic choices;
- configurable by rule, severity, and density threshold;
- suitable for local use, pre-commit, and CI annotations.

It ignores code fences, inline code, raw code blocks, URLs, front matter, comments, blockquotes, tables, link destinations, and MDX tags. Repetition rules reset at heading boundaries so templated API reference sections do not look like monotonous prose.

### Install

Add the hook to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/ysawa0/pre-commit
    rev: v0.2.0
    hooks:
      - id: anti-slop
```

Then run:

```console
pre-commit install
pre-commit run anti-slop --all-files
```

The recommended preset reports high-confidence writing problems as warnings. Informational findings remain visible but do not fail the hook. A mechanical artifact, such as pasted chatbot citation residue, is an error.

### Direct CLI use

```console
hooks/anti_slop.py README.md docs/*.md
hooks/anti_slop.py --preset strict README.md
hooks/anti_slop.py --format json README.md
hooks/anti_slop.py --format github README.md
hooks/anti_slop.py --list-rules
```

Exit status is `1` when a diagnostic reaches the configured failure level, `0` when the files pass, and `2` for configuration or input errors.

### Configuration

Place `.anti-slop.json` in the repository root:

```json
{
  "preset": "recommended",
  "fail_level": "warning",
  "rules": {
    "density.em-dash": {
      "severity": "warning",
      "max": 5,
      "window_words": 500
    },
    "phrase.marketing-language": "off"
  }
}
```

A rule can be `off`, `info`, `warning`, or `error`. Unknown rule names and option names fail closed instead of silently doing nothing.

### Local suppression

```markdown
<!-- anti-slop-disable-next-line verbosity.filler -->
In order to preserve a quoted legal term, keep this line unchanged.

<!-- anti-slop-disable rhetoric.* -->
This section intentionally uses repeated rhetorical structure.
<!-- anti-slop-enable rhetoric.* -->

This phrase is deliberate. <!-- anti-slop-ignore phrase.marketing-language -->
```

Selectors accept exact rule IDs, category wildcards such as `verbosity.*`, and `all`.

See [the anti-slop guide](docs/anti-slop.md) for the complete rule catalog and design notes. The [coffee calibration example](examples/anti-slop/README.md) shows the deliberately bloated input, the revised article, and the tuning results.

## Other hooks

- `terraform-fmt`: format Terraform files.
- `terraform-validate`: validate Terraform configuration.
- `packer-validate`: validate modern Packer templates.
- `terragrunt-hclfmt`: format Terragrunt configuration.
- `tflint`: lint Terraform source.
- `tfsec`: scan Terraform for security problems.
- `shellcheck`: lint shell scripts.
- `gofmt`: format Go source.
- `goimports`: format Go source and imports.
- `golint`: run the legacy Go linter.
- `yapf`: format Python source.
- `helmlint`: lint changed Helm charts.
- `markdown-link-check`: check links in Markdown.
- `check-terratest-skip-env`: reject uncommented Terratest skip environment variables.

Each hook can be selected in the same repository entry:

```yaml
repos:
  - repo: https://github.com/ysawa0/pre-commit
    rev: v0.2.0
    hooks:
      - id: anti-slop
      - id: terraform-fmt
      - id: tflint
      - id: shellcheck
```

## Helm lint caveat

`helmlint` searches upward from each changed file for `Chart.yaml` and runs once for each affected chart. A chart can provide `linter_values.yaml` for values that are required during linting but should not have production defaults.

## Shellcheck arguments

The shell hook accepts Shellcheck's `--enable` option:

```yaml
hooks:
  - id: shellcheck
    args: ["--enable", "require-variable-braces,deprecate-which"]
```

## Testing

```console
python -m unittest discover -s test -p '*_test.py' -v
python -m compileall -q hooks test
hooks/anti_slop.py --fail-level warning README.md docs/anti-slop.md examples/anti-slop/coffee-after.md
```

## License

This code is released under the Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
