#!/usr/bin/env python3
"""Entry point for the anti-slop Markdown prose linter."""

from __future__ import annotations

import os
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
if HOOK_DIR not in sys.path:
    sys.path.insert(0, HOOK_DIR)

from anti_slop_lib import (  # noqa: E402,F401
    ConfigError,
    Document,
    RULES,
    RULES_BY_ID,
    VERSION,
    lint_document,
    load_config,
)
from anti_slop_lib.cli import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
