#!/usr/bin/env python3
"""Music Video Pipeline CLI entry point."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli.commands import cli

if __name__ == "__main__":
    cli()
