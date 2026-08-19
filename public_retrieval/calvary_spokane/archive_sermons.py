#!/usr/bin/env python3
"""Source-tree entry point for the Calvary Spokane sermon archiver."""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from calvary_archive.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
