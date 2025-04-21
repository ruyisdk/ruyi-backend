"""
CLI management tool for the ruyi-backend package.
"""

import argparse
import asyncio
import logging
import sys
from typing import NoReturn

from ..config import get_env_config, init
from .cmd_sync_releases import do_sync_releases

def main(argv: list[str]) -> int:
    """Real entrypoint of ruyi-backend, allowing to customize argv."""

    init()
    cfg = get_env_config()

    logging.basicConfig(
        level=logging.DEBUG if cfg.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="ruyi-backend",
        description="CLI management client for RuyiSDK backend services.",
    )
    sp = parser.add_subparsers(title="subcommands", dest="command", required=True)

    sp.add_parser(
        "sync-releases",
        help="Release worker: sync releases from GitHub to the configured rsync destination.",
    )

    args = parser.parse_args(argv[1:])
    match args.command:
        case "sync-releases":
            return asyncio.run(do_sync_releases(cfg.cli.release_worker))

    return 0


def entrypoint() -> NoReturn:
    """Script entrypoint for the ruyi-backend CLI."""

    sys.exit(main(sys.argv))
