"""
CLI management tool for the ruyi-backend package.
"""

import sys
from typing import NoReturn


def main(argv: list[str]) -> int:
    """Real entrypoint of ruyi-backend, allowing to customize argv."""

    # TODO: do something
    print(f"Hello from ruyi-backend: {argv}")

    return 0


def entrypoint() -> NoReturn:
    """Script entrypoint for the ruyi-backend CLI."""

    sys.exit(main(sys.argv))
