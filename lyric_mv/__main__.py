"""Allows ``python -m lyric_mv <command>``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
